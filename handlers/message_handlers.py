"""
Message handlers for Telegram Temp Mail Bot
Handles text messages, documents, and other user inputs
"""

import logging
import re
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from config import (
    ERROR_MESSAGES,
    MAX_EMAIL_PREFIX_LENGTH,
    MIN_EMAIL_PREFIX_LENGTH
)
from keyboards.inline_keyboards import InlineKeyboards
from keyboards.reply_keyboards import ReplyKeyboards

logger = logging.getLogger(__name__)


class MessageHandlers:
    """Handler class for Telegram bot messages"""

    def __init__(self, mongo_client):
        """
        Initialize message handlers

        Args:
            mongo_client: MongoDB client instance
        """
        self.mongo_client = mongo_client

    async def text_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle text messages from reply keyboard or user input
        """
        try:
            message_text = update.message.text.strip()
            user_id = update.effective_user.id

            logger.info(f"User {user_id} sent text message: {message_text}")

            # Handle reply keyboard button presses
            if message_text == "📥 Inbox":
                await self._handle_inbox_button(update, context)
            elif message_text == "✉️ New Email":
                await self._handle_new_email_button(update, context)
            elif message_text == "🔁 Refresh":
                await self._handle_refresh_button(update, context)
            elif message_text == "🗑️ Delete":
                await self._handle_delete_button(update, context)
            elif message_text == "📖 Help":
                await self._handle_help_button(update, context)
            elif message_text == "⚙️ Settings":
                await self._handle_settings_button(update, context)
            elif message_text == "📊 Statistics":
                await self._handle_statistics_button(update, context)
            elif message_text == "🔙 Back" or message_text == "🏠 Home":
                await self._handle_back_button(update, context)
            elif message_text == "🔙 Main Menu":
                await self._handle_main_menu_button(update, context)
            elif message_text.startswith("✉️ Create"):
                await self._handle_create_email_button(update, context)
            elif message_text.startswith("📥 Check"):
                await self._handle_check_inbox_button(update, context)
            else:
                # Handle custom input (like email prefix)
                await self._handle_custom_input(update, context, message_text)

        except Exception as e:
            logger.error(f"Error in text_message_handler: {e}")
            await update.message.reply_text(
                ERROR_MESSAGES['general'],
                reply_markup=ReplyKeyboards.error_recovery_keyboard()
            )

    async def _handle_inbox_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Inbox button press"""
        try:
            # Import here to avoid circular imports
            from handlers.command_handlers import CommandHandlers

            # Reuse command handler logic
            command_handlers = CommandHandlers(self.mongo_client)
            await command_handlers.inbox_command(update, context)

        except Exception as e:
            logger.error(f"Error in _handle_inbox_button: {e}")
            await update.message.reply_text(
                ERROR_MESSAGES['general'],
                reply_markup=ReplyKeyboards.error_recovery_keyboard()
            )

    async def _handle_new_email_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle New Email button press"""
        try:
            # Import here to avoid circular imports
            from handlers.command_handlers import CommandHandlers

            # Reuse command handler logic
            command_handlers = CommandHandlers(self.mongo_client)
            await command_handlers.new_email_command(update, context)

        except Exception as e:
            logger.error(f"Error in _handle_new_email_button: {e}")
            await update.message.reply_text(
                ERROR_MESSAGES['general'],
                reply_markup=ReplyKeyboards.error_recovery_keyboard()
            )

    async def _handle_refresh_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Refresh button press"""
        try:
            # Import here to avoid circular imports
            from handlers.command_handlers import CommandHandlers

            # Reuse command handler logic
            command_handlers = CommandHandlers(self.mongo_client)
            await command_handlers.refresh_command(update, context)

        except Exception as e:
            logger.error(f"Error in _handle_refresh_button: {e}")
            await update.message.reply_text(
                ERROR_MESSAGES['general'],
                reply_markup=ReplyKeyboards.error_recovery_keyboard()
            )

    async def _handle_delete_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Delete button press"""
        try:
            # Import here to avoid circular imports
            from handlers.command_handlers import CommandHandlers

            # Reuse command handler logic
            command_handlers = CommandHandlers(self.mongo_client)
            await command_handlers.delete_command(update, context)

        except Exception as e:
            logger.error(f"Error in _handle_delete_button: {e}")
            await update.message.reply_text(
                ERROR_MESSAGES['general'],
                reply_markup=ReplyKeyboards.error_recovery_keyboard()
            )

    async def _handle_help_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Help button press"""
        try:
            # Import here to avoid circular imports
            from handlers.command_handlers import CommandHandlers

            # Reuse command handler logic
            command_handlers = CommandHandlers(self.mongo_client)
            await command_handlers.help_command(update, context)

        except Exception as e:
            logger.error(f"Error in _handle_help_button: {e}")
            await update.message.reply_text(
                "📖 Help temporarily unavailable.",
                reply_markup=ReplyKeyboards.main_reply_keyboard()
            )

    async def _handle_settings_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Settings button press"""
        try:
            await update.message.reply_text(
                "⚙️ <b>Settings</b>\n\n"
                "⏰ Email expiry: 1 hour\n"
                "🔔 Notifications: Enabled\n"
                "📊 Statistics: Enabled\n\n"
                "Settings customization coming soon!",
                parse_mode="HTML",
                reply_markup=InlineKeyboards.settings_keyboard()
            )

        except Exception as e:
            logger.error(f"Error in _handle_settings_button: {e}")
            await update.message.reply_text(
                ERROR_MESSAGES['general'],
                reply_markup=ReplyKeyboards.main_reply_keyboard()
            )

    async def _handle_statistics_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Statistics button press"""
        try:
            user_id = update.effective_user.id

            # Get user statistics
            stats = await self.mongo_client.get_user_statistics(user_id)

            if not stats:
                await update.message.reply_text(
                    "📊 <b>Statistics</b>\n\n"
                    "📧 No email history yet.\n"
                    "Create your first temporary email to start tracking!",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboards.single_button_keyboard(
                        "✉️ Create Email", "new_email"
                    )
                )
                return

            email = stats.get('email', 'Unknown')
            created_at = stats.get('created_at')
            expires_at = stats.get('expires_at')
            time_remaining = stats.get('time_remaining')
            message_count = stats.get('message_count', 0)
            total_messages = stats.get('total_messages_received', 0)
            is_active = stats.get('is_active', False)

            stats_text = [
                "📊 <b>Your Statistics</b>",
                "",
                f"📧 Current email: <code>{email}</code>",
                f"📬 Messages in inbox: {message_count}",
                f"📨 Total received: {total_messages}",
            ]

            if created_at:
                stats_text.append(f"📅 Created: {created_at.strftime('%Y-%m-%d %H:%M')}")

            if is_active and time_remaining:
                hours = int(time_remaining.total_seconds() // 3600)
                minutes = int((time_remaining.total_seconds() % 3600) // 60)
                stats_text.append(f"⏰ Expires in: {hours}h {minutes}m")
            elif not is_active:
                stats_text.append("❌ Email expired")

            await update.message.reply_text(
                "\n".join(stats_text),
                parse_mode="HTML",
                reply_markup=InlineKeyboards.statistics_keyboard()
            )

        except Exception as e:
            logger.error(f"Error in _handle_statistics_button: {e}")
            await update.message.reply_text(
                "📊 Statistics temporarily unavailable.",
                reply_markup=ReplyKeyboards.main_reply_keyboard()
            )

    async def _handle_back_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Back button press"""
        try:
            user_id = update.effective_user.id

            # Check if user has an active email
            user_data = await self.mongo_client.get_user(user_id)

            if user_data:
                email = user_data.get('email')
                await update.message.reply_text(
                    f"🔙 Back to main menu\n\n"
                    f"📧 Your email: <code>{email}</code>",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboards.main_actions_keyboard()
                )
            else:
                await update.message.reply_text(
                    "🔙 Back to main menu\n\n"
                    "Create a new email to get started!",
                    reply_markup=InlineKeyboards.welcome_keyboard()
                )

        except Exception as e:
            logger.error(f"Error in _handle_back_button: {e}")
            await update.message.reply_text(
                "🏠 Main Menu",
                reply_markup=ReplyKeyboards.main_reply_keyboard()
            )

    async def _handle_main_menu_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Main Menu button press"""
        try:
            user_id = update.effective_user.id

            # Check if user has an active email
            user_data = await self.mongo_client.get_user(user_id)

            if user_data:
                email = user_data.get('email')
                await update.message.reply_text(
                    "🏠 <b>Main Menu</b>\n\n"
                    f"📧 Your email: <code>{email}</code>\n\n"
                    "Choose an action below:",
                    parse_mode="HTML",
                    reply_markup=ReplyKeyboards.main_reply_keyboard()
                )
            else:
                await update.message.reply_text(
                    "🏠 <b>Main Menu</b>\n\n"
                    "Welcome to Temp Mail Bot!\n\n"
                    "Choose an action below:",
                    parse_mode="HTML",
                    reply_markup=ReplyKeyboards.welcome_keyboard()
                )

        except Exception as e:
            logger.error(f"Error in _handle_main_menu_button: {e}")
            await update.message.reply_text(
                "🏠 Main Menu",
                reply_markup=ReplyKeyboards.main_reply_keyboard()
            )

    async def _handle_create_email_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Create Email button press (various texts)"""
        try:
            # Import here to avoid circular imports
            from handlers.command_handlers import CommandHandlers

            # Reuse command handler logic
            command_handlers = CommandHandlers(self.mongo_client)
            await command_handlers.new_email_command(update, context)

        except Exception as e:
            logger.error(f"Error in _handle_create_email_button: {e}")
            await update.message.reply_text(
                ERROR_MESSAGES['general'],
                reply_markup=ReplyKeyboards.error_recovery_keyboard()
            )

    async def _handle_check_inbox_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Check Inbox button press (various texts)"""
        try:
            # Import here to avoid circular imports
            from handlers.command_handlers import CommandHandlers

            # Reuse command handler logic
            command_handlers = CommandHandlers(self.mongo_client)
            await command_handlers.inbox_command(update, context)

        except Exception as e:
            logger.error(f"Error in _handle_check_inbox_button: {e}")
            await update.message.reply_text(
                ERROR_MESSAGES['general'],
                reply_markup=ReplyKeyboards.error_recovery_keyboard()
            )

    async def _handle_custom_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """
        Handle custom user input that doesn't match predefined buttons
        """
        try:
            text = text.strip()

            # Check if it might be an email prefix request
            if self._is_valid_prefix_input(text):
                await self._handle_email_prefix_request(update, context, text)
                return

            # Check for other common patterns
            if text.lower() in ['hello', 'hi', 'hey']:
                await self._handle_greeting(update, context)
                return

            if text.lower() in ['bye', 'goodbye', 'exit']:
                await self._handle_goodbye(update, context)
                return

            # Default response for unrecognized input
            await self._handle_unrecognized_input(update, context)

        except Exception as e:
            logger.error(f"Error in _handle_custom_input: {e}")
            await update.message.reply_text(
                "❓ I didn't understand that. Use the buttons below or type /help for commands.",
                reply_markup=ReplyKeyboards.main_reply_keyboard()
            )

    def _is_valid_prefix_input(self, text: str) -> bool:
        """
        Check if input might be a valid email prefix request
        """
        # Remove spaces and convert to lowercase
        clean_text = re.sub(r'\s+', '', text.lower())

        # Check if it's alphanumeric and reasonable length
        if (clean_text.isalnum() and
            MIN_EMAIL_PREFIX_LENGTH <= len(clean_text) <= MAX_EMAIL_PREFIX_LENGTH):
            return True

        # Check if it contains 'email' or 'prefix' keywords
        keywords = ['email', 'prefix', 'name', 'address']
        if any(keyword in text.lower() for keyword in keywords):
            return True

        return False

    async def _handle_email_prefix_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, prefix: str):
        """Handle user request for custom email prefix"""
        try:
            user_id = update.effective_user.id

            # Clean the prefix
            clean_prefix = ''.join(c for c in prefix.lower() if c.isalnum())
            clean_prefix = clean_prefix[:MAX_EMAIL_PREFIX_LENGTH]

            if len(clean_prefix) < MIN_EMAIL_PREFIX_LENGTH:
                await update.message.reply_text(
                    f"❌ Prefix too short. Use at least {MIN_EMAIL_PREFIX_LENGTH} characters.",
                    reply_markup=ReplyKeyboards.main_reply_keyboard()
                )
                return

            # Import email generator
            from email.email_generator import EmailGenerator
            email_generator = EmailGenerator(self.mongo_client)

            # Validate the prefix
            validation_result = email_generator.validate_custom_prefix(clean_prefix)

            if validation_result['valid']:
                # Generate email with custom prefix
                result = await email_generator.generate_email_with_validation(user_id, clean_prefix)

                if result['success']:
                    email = result['email']
                    prefix_used = result['prefix']

                    # Create user in database
                    user_doc = await self.mongo_client.create_user(user_id, email, prefix_used)

                    if user_doc:
                        await update.message.reply_text(
                            f"✅ Email created with custom prefix!\n\n"
                            f"📧 <code>{email}</code>\n\n"
                            f"⏰ Valid for 1 hour",
                            parse_mode="HTML",
                            reply_markup=InlineKeyboards.share_email_keyboard(email)
                        )
                    else:
                        await update.message.reply_text(
                            "❌ Failed to create email. Please try again.",
                            reply_markup=ReplyKeyboards.main_reply_keyboard()
                        )
                else:
                    error_type = result.get('error', 'generation_failed')
                    if error_type == 'user_already_has_email':
                        existing_email = result.get('existing_email')
                        await update.message.reply_text(
                            f"⚠️ You already have an active email:\n"
                            f"<code>{existing_email}</code>",
                            parse_mode="HTML",
                            reply_markup=InlineKeyboards.main_actions_keyboard()
                        )
                    else:
                        await update.message.reply_text(
                            "❌ Failed to generate email. Please try again.",
                            reply_markup=ReplyKeyboards.main_reply_keyboard()
                        )
            else:
                await update.message.reply_text(
                    f"❌ Invalid prefix: {validation_result['message']}",
                    reply_markup=ReplyKeyboards.main_reply_keyboard()
                )

        except Exception as e:
            logger.error(f"Error in _handle_email_prefix_request: {e}")
            await update.message.reply_text(
                "❌ Error processing your request. Please try again.",
                reply_markup=ReplyKeyboards.main_reply_keyboard()
            )

    async def _handle_greeting(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle greeting messages"""
        try:
            user = update.effective_user
            user_name = user.first_name if user.first_name else "there"

            await update.message.reply_text(
                f"👋 Hello {user_name}!\n\n"
                "Use the buttons below to manage your temporary email, or type /help for commands.",
                reply_markup=ReplyKeyboards.main_reply_keyboard()
            )

        except Exception as e:
            logger.error(f"Error in _handle_greeting: {e}")

    async def _handle_goodbye(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle goodbye messages"""
        try:
            user = update.effective_user
            user_name = user.first_name if user.first_name else "there"

            await update.message.reply_text(
                f"👋 Goodbye {user_name}!\n\n"
                "Your temporary emails will continue working until they expire.\n"
                "Come back anytime!",
                reply_markup=ReplyKeyboards.remove_keyboard()
            )

        except Exception as e:
            logger.error(f"Error in _handle_goodbye: {e}")

    async def _handle_unrecognized_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unrecognized user input"""
        try:
            await update.message.reply_text(
                "🤔 I didn't understand that.\n\n"
                "Use the buttons below or type:\n"
                "/help - for available commands\n"
                "/new - create new email\n"
                "/inbox - check your inbox",
                reply_markup=ReplyKeyboards.main_reply_keyboard()
            )

        except Exception as e:
            logger.error(f"Error in _handle_unrecognized_input: {e}")

    async def document_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle document messages
        """
        try:
            await update.message.reply_text(
                "📄 I can't receive documents.\n\n"
                "This bot only creates temporary email addresses and forwards emails to you.\n"
                "Use the buttons below to manage your emails.",
                reply_markup=ReplyKeyboards.main_reply_keyboard()
            )

        except Exception as e:
            logger.error(f"Error in document_handler: {e}")

    async def photo_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle photo messages
        """
        try:
            await update.message.reply_text(
                "🖼️ I can't receive photos.\n\n"
                "This bot only creates temporary email addresses and forwards emails to you.\n"
                "Use the buttons below to manage your emails.",
                reply_markup=ReplyKeyboards.main_reply_keyboard()
            )

        except Exception as e:
            logger.error(f"Error in photo_handler: {e}")

    async def audio_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle audio messages
        """
        try:
            await update.message.reply_text(
                "🎵 I can't receive audio.\n\n"
                "This bot only creates temporary email addresses and forwards emails to you.\n"
                "Use the buttons below to manage your emails.",
                reply_markup=ReplyKeyboards.main_reply_keyboard()
            )

        except Exception as e:
            logger.error(f"Error in audio_handler: {e}")

    async def video_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle video messages
        """
        try:
            await update.message.reply_text(
                "🎥 I can't receive videos.\n\n"
                "This bot only creates temporary email addresses and forwards emails to you.\n"
                "Use the buttons below to manage your emails.",
                reply_markup=ReplyKeyboards.main_reply_keyboard()
            )

        except Exception as e:
            logger.error(f"Error in video_handler: {e}")

    async def location_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle location messages
        """
        try:
            await update.message.reply_text(
                "📍 I can't process locations.\n\n"
                "This bot only creates temporary email addresses and forwards emails to you.\n"
                "Use the buttons below to manage your emails.",
                reply_markup=ReplyKeyboards.main_reply_keyboard()
            )

        except Exception as e:
            logger.error(f"Error in location_handler: {e}")

    async def contact_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle contact messages
        """
        try:
            await update.message.reply_text(
                "📞 I can't process contacts.\n\n"
                "This bot only creates temporary email addresses and forwards emails to you.\n"
                "Use the buttons below to manage your emails.",
                reply_markup=ReplyKeyboards.main_reply_keyboard()
            )

        except Exception as e:
            logger.error(f"Error in contact_handler: {e}")