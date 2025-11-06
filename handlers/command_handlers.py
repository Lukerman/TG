"""
Command handlers for Telegram Temp Mail Bot
Handles all Telegram bot commands (/start, /new, /inbox, etc.)
"""

import logging
import asyncio
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from config import (
    WELCOME_MESSAGE,
    HELP_MESSAGE,
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,
    MAX_INBOX_MESSAGES,
    LOADING_MESSAGES
)
from email_services.email_generator import EmailGenerator
from email_services.imap_client import IMAPClient
from email_services.email_parser import EmailParser
from keyboards.inline_keyboards import InlineKeyboards
from keyboards.reply_keyboards import ReplyKeyboards

logger = logging.getLogger(__name__)


class CommandHandlers:
    """Handler class for Telegram bot commands"""

    def __init__(self, mongo_client):
        """
        Initialize command handlers

        Args:
            mongo_client: MongoDB client instance
        """
        self.mongo_client = mongo_client
        self.email_generator = EmailGenerator(mongo_client)
        self.imap_client = IMAPClient()
        self.email_parser = EmailParser()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /start command
        Shows welcome message and creates initial setup
        """
        try:
            user = update.effective_user
            user_id = user.id

            logger.info(f"User {user_id} ({user.username}) started the bot")

            # Send welcome message
            await update.message.reply_text(
                WELCOME_MESSAGE,
                parse_mode="HTML",
                reply_markup=InlineKeyboards.welcome_keyboard()
            )

            # Set main reply keyboard
            await update.message.reply_text(
                "Use the buttons below or type commands:",
                reply_markup=ReplyKeyboards.main_reply_keyboard()
            )

            # Check if user already has an active email
            existing_user = await self.mongo_client.get_user(user_id)
            if existing_user:
                email = existing_user.get('email')
                expires_at = existing_user.get('expires_at')

                # Calculate remaining time
                if expires_at:
                    now = datetime.utcnow()
                    if expires_at > now:
                        time_diff = expires_at - now
                        hours = time_diff.total_seconds() // 3600
                        minutes = (time_diff.total_seconds() % 3600) // 60

                        await update.message.reply_text(
                            f"✅ You already have an active email:\n\n"
                            f"📧 <code>{email}</code>\n"
                            f"⏰ Expires in {int(hours)}h {int(minutes)}m",
                            parse_mode="HTML",
                            reply_markup=InlineKeyboards.share_email_keyboard(email)
                        )
                    else:
                        await update.message.reply_text(
                            "⏰ Your previous email has expired.\n"
                            "Use the button below to create a new one.",
                            reply_markup=InlineKeyboards.single_button_keyboard(
                                "✉️ Create New Email", "new_email"
                            )
                        )
                else:
                    await update.message.reply_text(
                        "⚠️ Your email setup seems incomplete.\n"
                        "Use the button below to create a new email.",
                        reply_markup=InlineKeyboards.single_button_keyboard(
                            "✉️ Create New Email", "new_email"
                        )
                    )

        except Exception as e:
            logger.error(f"Error in start_command: {e}")
            await update.message.reply_text(
                ERROR_MESSAGES['general'],
                reply_markup=ReplyKeyboards.error_recovery_keyboard()
            )

    async def new_email_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /new command
        Creates a new temporary email address
        """
        try:
            user = update.effective_user
            user_id = user.id

            logger.info(f"User {user_id} requested new email")

            # Send loading message
            loading_message = await update.message.reply_text(
                "⏳ Generating your temporary email...",
                reply_markup=InlineKeyboards.loading_keyboard("new_email")
            )

            # Generate email with validation
            result = await self.email_generator.generate_email_with_validation(user_id)

            # Delete loading message
            try:
                await loading_message.delete()
            except:
                pass

            if result['success']:
                email = result['email']
                prefix = result['prefix']

                # Create user in database
                user_doc = await self.mongo_client.create_user(user_id, email, prefix)

                if user_doc:
                    # Send success message with email
                    await update.message.reply_text(
                        f"✅ {SUCCESS_MESSAGES['email_created']}\n\n"
                        f"📧 Your temporary email:\n"
                        f"<code>{email}</code>\n\n"
                        f"⏰ Valid for 1 hour\n"
                        f"📥 Ready to receive emails!",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboards.share_email_keyboard(email)
                    )
                else:
                    raise Exception("Failed to create user in database")
            else:
                error_type = result.get('error', 'generation_failed')
                error_message = result.get('message', ERROR_MESSAGES[error_type])

                if error_type == 'user_already_has_email':
                    existing_email = result.get('existing_email')
                    await update.message.reply_text(
                        f"⚠️ You already have an active email:\n"
                        f"<code>{existing_email}</code>\n\n"
                        f"Use /delete first if you want a new one.",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboards.main_actions_keyboard()
                    )
                else:
                    await update.message.reply_text(
                        f"❌ {error_message}\n"
                        f"Please try again later.",
                        reply_markup=InlineKeyboards.error_keyboard(error_type)
                    )

        except Exception as e:
            logger.error(f"Error in new_email_command: {e}")
            await update.message.reply_text(
                ERROR_MESSAGES['generation_failed'],
                reply_markup=InlineKeyboards.error_keyboard('general')
            )

    async def inbox_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /inbox command
        Shows user's email inbox
        """
        try:
            user = update.effective_user
            user_id = user.id

            logger.info(f"User {user_id} requested inbox")

            # Check if user has an active email
            user_data = await self.mongo_client.get_user(user_id)
            if not user_data:
                await update.message.reply_text(
                    ERROR_MESSAGES['no_email'],
                    reply_markup=InlineKeyboards.single_button_keyboard(
                        "✉️ Create Email", "new_email"
                    )
                )
                return

            email = user_data.get('email')
            if not email:
                await update.message.reply_text(
                    ERROR_MESSAGES['no_email'],
                    reply_markup=InlineKeyboards.single_button_keyboard(
                        "✉️ Create Email", "new_email"
                    )
                )
                return

            # Send loading message
            loading_message = await update.message.reply_text(
                "🔄 Checking your inbox...",
                reply_markup=InlineKeyboards.loading_keyboard("inbox")
            )

            try:
                # Connect to IMAP and fetch emails
                await self.imap_client.ensure_connection()

                # Get user's last checked time
                last_checked = user_data.get('last_checked', datetime.utcnow())

                # Fetch messages
                messages = await self.imap_client.fetch_message_list(
                    email,
                    limit=MAX_INBOX_MESSAGES,
                    since_date=last_checked
                )

                # Update last checked timestamp
                await self.mongo_client.update_last_checked(user_id)

                # Delete loading message
                try:
                    await loading_message.delete()
                except:
                    pass

                if messages:
                    # Format inbox display
                    await self._display_inbox(update, messages, email)
                else:
                    await update.message.reply_text(
                        "📭 Your inbox is empty.\n\n"
                        "📧 Your email: <code>{email}</code>\n"
                        "🔄 Check back later for new messages!",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboards.empty_state_keyboard()
                    )

            except Exception as imap_error:
                logger.error(f"IMAP error in inbox_command: {imap_error}")
                # Delete loading message
                try:
                    await loading_message.delete()
                except:
                    pass

                await update.message.reply_text(
                    ERROR_MESSAGES['imap_error'],
                    reply_markup=InlineKeyboards.error_keyboard('connection')
                )

        except Exception as e:
            logger.error(f"Error in inbox_command: {e}")
            await update.message.reply_text(
                ERROR_MESSAGES['general'],
                reply_markup=InlineKeyboards.error_keyboard('general')
            )

    async def refresh_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /refresh command
        Refreshes user's inbox
        """
        try:
            user = update.effective_user
            user_id = user.id

            logger.info(f"User {user_id} requested refresh")

            # Delegate to inbox command since they do the same thing
            await self.inbox_command(update, context)

        except Exception as e:
            logger.error(f"Error in refresh_command: {e}")
            await update.message.reply_text(
                ERROR_MESSAGES['general'],
                reply_markup=InlineKeyboards.error_keyboard('general')
            )

    async def delete_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /delete command
        Deletes user's temporary email
        """
        try:
            user = update.effective_user
            user_id = user.id

            logger.info(f"User {user_id} requested email deletion")

            # Check if user has an active email
            user_data = await self.mongo_client.get_user(user_id)
            if not user_data:
                await update.message.reply_text(
                    ERROR_MESSAGES['no_email'],
                    reply_markup=InlineKeyboards.single_button_keyboard(
                        "✉️ Create Email", "new_email"
                    )
                )
                return

            email = user_data.get('email')

            await update.message.reply_text(
                f"⚠️ Are you sure you want to delete your temporary email?\n\n"
                f"📧 <code>{email}</code>\n\n"
                f"This action cannot be undone!",
                parse_mode="HTML",
                reply_markup=InlineKeyboards.confirmation_keyboard("delete_email")
            )

        except Exception as e:
            logger.error(f"Error in delete_command: {e}")
            await update.message.reply_text(
                ERROR_MESSAGES['general'],
                reply_markup=InlineKeyboards.error_keyboard('general')
            )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /help command
        Shows help information
        """
        try:
            logger.info(f"User {update.effective_user.id} requested help")

            await update.message.reply_text(
                HELP_MESSAGE,
                parse_mode="HTML",
                reply_markup=InlineKeyboards.help_keyboard()
            )

        except Exception as e:
            logger.error(f"Error in help_command: {e}")
            await update.message.reply_text(
                ERROR_MESSAGES['general'],
                reply_markup=ReplyKeyboards.error_recovery_keyboard()
            )

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /status command
        Shows user's current status
        """
        try:
            user = update.effective_user
            user_id = user.id

            logger.info(f"User {user_id} requested status")

            # Get user statistics
            stats = await self.mongo_client.get_user_statistics(user_id)

            if not stats:
                await update.message.reply_text(
                    "❓ You don't have any temporary emails yet.\n"
                    "Use /new to create your first temporary email!",
                    reply_markup=InlineKeyboards.single_button_keyboard(
                        "✉️ Create Email", "new_email"
                    )
                )
                return

            # Format status message
            email = stats.get('email', 'Unknown')
            created_at = stats.get('created_at')
            expires_at = stats.get('expires_at')
            time_remaining = stats.get('time_remaining')
            message_count = stats.get('message_count', 0)
            total_messages = stats.get('total_messages_received', 0)
            is_active = stats.get('is_active', False)

            status_text = [
                "📊 <b>Your Email Status</b>",
                "",
                f"📧 Email: <code>{email}</code>",
            ]

            if is_active and time_remaining:
                hours = int(time_remaining.total_seconds() // 3600)
                minutes = int((time_remaining.total_seconds() % 3600) // 60)
                status_text.append(f"⏰ Time remaining: {hours}h {minutes}m")
            elif is_active:
                status_text.append("⏰ Active (time unknown)")
            else:
                status_text.append("❌ Email expired")

            if created_at:
                status_text.append(f"📅 Created: {created_at.strftime('%Y-%m-%d %H:%M')}")

            status_text.extend([
                f"📬 Messages in inbox: {message_count}",
                f"📨 Total received: {total_messages}",
            ])

            await update.message.reply_text(
                "\n".join(status_text),
                parse_mode="HTML",
                reply_markup=InlineKeyboards.main_actions_keyboard()
            )

        except Exception as e:
            logger.error(f"Error in status_command: {e}")
            await update.message.reply_text(
                ERROR_MESSAGES['general'],
                reply_markup=InlineKeyboards.error_keyboard('general')
            )

    async def _display_inbox(self, update: Update, messages: list, email: str):
        """
        Display inbox messages to user

        Args:
            update: Telegram update object
            messages: List of message dictionaries
            email: User's email address
        """
        try:
            if not messages:
                await update.message.reply_text(
                    f"📭 Your inbox is empty.\n\n"
                    f"📧 Email: <code>{email}</code>",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboards.empty_state_keyboard()
                )
                return

            # Create inbox header
            header_text = f"📥 <b>Your Inbox ({len(messages)} messages)</b>\n\n"
            header_text += f"📧 <code>{email}</code>\n"

            await update.message.reply_text(
                header_text,
                parse_mode="HTML"
            )

            # Send message previews
            for i, message_data in enumerate(messages, 1):
                preview = self.email_parser.format_message_preview(message_data)

                # Add message number
                numbered_preview = f"<b>{i}.</b> {preview}"

                await update.message.reply_text(
                    numbered_preview,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboards.email_actions_keyboard(
                        message_data.get('uid', str(i)),
                        message_data.get('has_attachments', False)
                    )
                )

            # Send action buttons at the end
            await update.message.reply_text(
                "💡 Use the buttons above to view messages or download attachments",
                reply_markup=InlineKeyboards.main_actions_keyboard()
            )

        except Exception as e:
            logger.error(f"Error displaying inbox: {e}")
            raise