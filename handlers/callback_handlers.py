"""
Callback handlers for Telegram Temp Mail Bot
Handles all inline button callback queries
"""

import logging
import asyncio
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InputFile
from telegram.ext import ContextTypes

from config import (
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,
    MAX_INBOX_MESSAGES
)
from email_services.email_generator import EmailGenerator
from email_services.imap_client import IMAPClient
from email_services.email_parser import EmailParser
from keyboards.inline_keyboards import InlineKeyboards
from keyboards.reply_keyboards import ReplyKeyboards

logger = logging.getLogger(__name__)


class CallbackHandlers:
    """Handler class for Telegram bot callback queries"""

    def __init__(self, mongo_client):
        """
        Initialize callback handlers

        Args:
            mongo_client: MongoDB client instance
        """
        self.mongo_client = mongo_client
        self.email_generator = EmailGenerator(mongo_client)
        self.imap_client = IMAPClient()
        self.email_parser = EmailParser()

    async def callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Main callback handler
        Routes callbacks to appropriate handler methods
        """
        try:
            query = update.callback_query
            await query.answer()  # Acknowledge the callback

            callback_data = query.data
            user_id = update.effective_user.id

            logger.info(f"User {user_id} triggered callback: {callback_data}")

            # Route callback to appropriate handler
            if callback_data == "new_email":
                await self.handle_new_email(update, context)
            elif callback_data == "refresh_inbox":
                await self.handle_refresh_inbox(update, context)
            elif callback_data == "delete_email":
                await self.handle_delete_email(update, context)
            elif callback_data.startswith("view_message:"):
                await self.handle_view_message(update, context)
            elif callback_data.startswith("download_attachments:"):
                await self.handle_download_attachments(update, context)
            elif callback_data.startswith("download_attachment:"):
                await self.handle_download_single_attachment(update, context)
            elif callback_data.startswith("confirm_delete"):
                await self.handle_confirm_delete(update, context)
            elif callback_data.startswith("cancel_"):
                await self.handle_cancel_action(update, context)
            elif callback_data == "help":
                await self.handle_help(update, context)
            elif callback_data.startswith("copy_email:"):
                await self.handle_copy_email(update, context)
            elif callback_data.startswith("share_email:"):
                await self.handle_share_email(update, context)
            elif callback_data.startswith("loading_"):
                await self.handle_loading_callback(update, context)
            else:
                await self.handle_unknown_callback(update, context)

        except Exception as e:
            logger.error(f"Error in callback_handler: {e}")
            try:
                await update.callback_query.edit_message_text(
                    ERROR_MESSAGES['general'],
                    reply_markup=InlineKeyboards.error_keyboard('general')
                )
            except:
                pass

    async def handle_new_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle new email creation callback"""
        try:
            user_id = update.effective_user.id

            # Edit the original message to show loading
            await update.callback_query.edit_message_text(
                "⏳ Creating your new temporary email...",
                reply_markup=InlineKeyboards.loading_keyboard("new_email")
            )

            # Generate email
            result = await self.email_generator.generate_email_with_validation(user_id)

            if result['success']:
                email = result['email']
                prefix = result['prefix']

                # Create user in database
                user_doc = await self.mongo_client.create_user(user_id, email, prefix)

                if user_doc:
                    await update.callback_query.edit_message_text(
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
                    await update.callback_query.edit_message_text(
                        f"⚠️ You already have an active email:\n"
                        f"<code>{existing_email}</code>\n\n"
                        f"Delete it first if you want a new one.",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboards.main_actions_keyboard()
                    )
                else:
                    await update.callback_query.edit_message_text(
                        f"❌ {error_message}",
                        reply_markup=InlineKeyboards.error_keyboard(error_type)
                    )

        except Exception as e:
            logger.error(f"Error in handle_new_email: {e}")
            await update.callback_query.edit_message_text(
                ERROR_MESSAGES['generation_failed'],
                reply_markup=InlineKeyboards.error_keyboard('general')
            )

    async def handle_refresh_inbox(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inbox refresh callback"""
        try:
            user_id = update.effective_user.id

            # Check if user has an active email
            user_data = await self.mongo_client.get_user(user_id)
            if not user_data:
                await update.callback_query.edit_message_text(
                    ERROR_MESSAGES['no_email'],
                    reply_markup=InlineKeyboards.single_button_keyboard(
                        "✉️ Create Email", "new_email"
                    )
                )
                return

            email = user_data.get('email')

            # Edit message to show loading
            await update.callback_query.edit_message_text(
                "🔄 Checking your inbox...",
                reply_markup=InlineKeyboards.loading_keyboard("refresh")
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

                if messages:
                    # Display inbox
                    await self._display_inbox_callback(update, messages, email)
                else:
                    await update.callback_query.edit_message_text(
                        f"📭 Your inbox is empty.\n\n"
                        f"📧 Email: <code>{email}</code>\n\n"
                        f"🔄 Check back later!",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboards.empty_state_keyboard()
                    )

            except Exception as imap_error:
                logger.error(f"IMAP error in handle_refresh_inbox: {imap_error}")
                await update.callback_query.edit_message_text(
                    ERROR_MESSAGES['imap_error'],
                    reply_markup=InlineKeyboards.error_keyboard('connection')
                )

        except Exception as e:
            logger.error(f"Error in handle_refresh_inbox: {e}")
            await update.callback_query.edit_message_text(
                ERROR_MESSAGES['general'],
                reply_markup=InlineKeyboards.error_keyboard('general')
            )

    async def handle_view_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle view message callback"""
        try:
            user_id = update.effective_user.id
            callback_data = update.callback_query.data
            uid = callback_data.split(":", 1)[1]

            # Get user data
            user_data = await self.mongo_client.get_user(user_id)
            if not user_data:
                await update.callback_query.edit_message_text(
                    ERROR_MESSAGES['no_email'],
                    reply_markup=InlineKeyboards.single_button_keyboard(
                        "✉️ Create Email", "new_email"
                    )
                )
                return

            email = user_data.get('email')

            # Edit message to show loading
            await update.callback_query.edit_message_text(
                "📧 Loading message...",
                reply_markup=InlineKeyboards.loading_keyboard("view_message")
            )

            try:
                # Connect to IMAP
                await self.imap_client.ensure_connection()

                # Fetch specific message
                message_data = await self.imap_client.fetch_message(uid)

                if message_data:
                    # Format full message
                    full_message = self.email_parser.format_full_message(message_data)

                    # Split message if too long for Telegram
                    max_length = 4000  # Leave room for formatting
                    if len(full_message) > max_length:
                        # Send first part
                        await update.callback_query.edit_message_text(
                            full_message[:max_length] + "\n\n<i>... Message continues</i>",
                            parse_mode="HTML",
                            reply_markup=InlineKeyboards.email_actions_keyboard(
                                uid,
                                message_data.get('has_attachments', False)
                            )
                        )
                    else:
                        await update.callback_query.edit_message_text(
                            full_message,
                            parse_mode="HTML",
                            reply_markup=InlineKeyboards.email_actions_keyboard(
                                uid,
                                message_data.get('has_attachments', False)
                            )
                        )
                else:
                    await update.callback_query.edit_message_text(
                        "❌ Failed to load message. It may have been deleted.",
                        reply_markup=InlineKeyboards.single_button_keyboard(
                            "🔙 Back to Inbox", "refresh_inbox"
                        )
                    )

            except Exception as imap_error:
                logger.error(f"IMAP error in handle_view_message: {imap_error}")
                await update.callback_query.edit_message_text(
                    ERROR_MESSAGES['imap_error'],
                    reply_markup=InlineKeyboards.error_keyboard('connection')
                )

        except Exception as e:
            logger.error(f"Error in handle_view_message: {e}")
            await update.callback_query.edit_message_text(
                ERROR_MESSAGES['general'],
                reply_markup=InlineKeyboards.error_keyboard('general')
            )

    async def handle_download_attachments(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle download all attachments callback"""
        try:
            user_id = update.effective_user.id
            callback_data = update.callback_query.data
            uid = callback_data.split(":", 1)[1]

            # Get user data
            user_data = await self.mongo_client.get_user(user_id)
            if not user_data:
                await update.callback_query.edit_message_text(
                    ERROR_MESSAGES['no_email'],
                    reply_markup=InlineKeyboards.single_button_keyboard(
                        "✉️ Create Email", "new_email"
                    )
                )
                return

            # Edit message to show loading
            await update.callback_query.edit_message_text(
                "📎 Preparing attachments...",
                reply_markup=InlineKeyboards.loading_keyboard("attachments")
            )

            try:
                # Connect to IMAP
                await self.imap_client.ensure_connection()

                # Fetch message
                message_data = await self.imap_client.fetch_message(uid)

                if not message_data:
                    await update.callback_query.edit_message_text(
                        "❌ Failed to load message.",
                        reply_markup=InlineKeyboards.single_button_keyboard(
                            "🔙 Back to Inbox", "refresh_inbox"
                        )
                    )
                    return

                attachments = message_data.get('attachments', [])

                if not attachments:
                    await update.callback_query.edit_message_text(
                        "📎 This message has no attachments.",
                        reply_markup=InlineKeyboards.email_actions_keyboard(uid, False)
                    )
                    return

                # Send attachments one by one
                await update.callback_query.edit_message_text(
                    f"📎 Found {len(attachments)} attachment(s). Sending them now...",
                    reply_markup=None
                )

                for i, attachment in enumerate(attachments):
                    try:
                        # Prepare attachment for Telegram
                        prepared_attachment = await self.email_parser.prepare_attachment_for_telegram(attachment)

                        if prepared_attachment:
                            # Send attachment
                            with open(prepared_attachment['path'], 'rb') as file:
                                if prepared_attachment['is_image']:
                                    await context.bot.send_photo(
                                        chat_id=update.effective_chat.id,
                                        photo=file,
                                        caption=f"📎 {attachment.get('filename', 'image')}"
                                    )
                                else:
                                    await context.bot.send_document(
                                        chat_id=update.effective_chat.id,
                                        document=file,
                                        caption=f"📎 {attachment.get('filename', 'document')}"
                                    )
                        else:
                            await context.bot.send_message(
                                chat_id=update.effective_chat.id,
                                text=f"❌ Failed to prepare attachment: {attachment.get('filename', 'unknown')}"
                            )

                    except Exception as attachment_error:
                        logger.error(f"Error sending attachment {i}: {attachment_error}")
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text=f"❌ Error sending attachment: {attachment.get('filename', 'unknown')}"
                        )

                # Send completion message
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"✅ Sent {len(attachments)} attachment(s)",
                    reply_markup=InlineKeyboards.email_actions_keyboard(uid, True)
                )

                # Clean up temporary files
                await self.email_parser.cleanup_temp_files()

            except Exception as imap_error:
                logger.error(f"IMAP error in handle_download_attachments: {imap_error}")
                await update.callback_query.edit_message_text(
                    ERROR_MESSAGES['imap_error'],
                    reply_markup=InlineKeyboards.error_keyboard('connection')
                )

        except Exception as e:
            logger.error(f"Error in handle_download_attachments: {e}")
            await update.callback_query.edit_message_text(
                ERROR_MESSAGES['attachment_error'],
                reply_markup=InlineKeyboards.error_keyboard('general')
            )

    async def handle_download_single_attachment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle download single attachment callback"""
        try:
            user_id = update.effective_user.id
            callback_data = update.callback_query.data
            parts = callback_data.split(":")
            uid = parts[1]
            attachment_index = int(parts[2]) if len(parts) > 2 else 0

            # Get user data
            user_data = await self.mongo_client.get_user(user_id)
            if not user_data:
                await update.callback_query.answer("No active email found", show_alert=True)
                return

            # Answer the callback to remove loading state
            await update.callback_query.answer("📎 Preparing attachment...")

            try:
                # Connect to IMAP
                await self.imap_client.ensure_connection()

                # Fetch message
                message_data = await self.imap_client.fetch_message(uid)

                if not message_data:
                    await update.callback_query.answer("❌ Failed to load message", show_alert=True)
                    return

                attachments = message_data.get('attachments', [])

                if attachment_index >= len(attachments):
                    await update.callback_query.answer("❌ Attachment not found", show_alert=True)
                    return

                attachment = attachments[attachment_index]

                # Prepare attachment for Telegram
                prepared_attachment = await self.email_parser.prepare_attachment_for_telegram(attachment)

                if prepared_attachment:
                    # Send attachment
                    with open(prepared_attachment['path'], 'rb') as file:
                        if prepared_attachment['is_image']:
                            await context.bot.send_photo(
                                chat_id=update.effective_chat.id,
                                photo=file,
                                caption=f"📎 {attachment.get('filename', 'image')}"
                            )
                        else:
                            await context.bot.send_document(
                                chat_id=update.effective_chat.id,
                                document=file,
                                caption=f"📎 {attachment.get('filename', 'document')}"
                            )

                    await update.callback_query.answer("✅ Attachment sent!", show_alert=False)
                else:
                    await update.callback_query.answer("❌ Failed to prepare attachment", show_alert=True)

                # Clean up temporary files
                await self.email_parser.cleanup_temp_files()

            except Exception as attachment_error:
                logger.error(f"Error sending single attachment: {attachment_error}")
                await update.callback_query.answer("❌ Error sending attachment", show_alert=True)

        except Exception as e:
            logger.error(f"Error in handle_download_single_attachment: {e}")
            await update.callback_query.answer("❌ Error processing attachment", show_alert=True)

    async def handle_delete_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle delete email callback"""
        try:
            user_id = update.effective_user.id

            # Check if user has an active email
            user_data = await self.mongo_client.get_user(user_id)
            if not user_data:
                await update.callback_query.edit_message_text(
                    ERROR_MESSAGES['no_email'],
                    reply_markup=InlineKeyboards.single_button_keyboard(
                        "✉️ Create Email", "new_email"
                    )
                )
                return

            email = user_data.get('email')

            await update.callback_query.edit_message_text(
                f"⚠️ Are you sure you want to delete your temporary email?\n\n"
                f"📧 <code>{email}</code>\n\n"
                f"This action cannot be undone!",
                parse_mode="HTML",
                reply_markup=InlineKeyboards.confirmation_keyboard("delete_email")
            )

        except Exception as e:
            logger.error(f"Error in handle_delete_email: {e}")
            await update.callback_query.edit_message_text(
                ERROR_MESSAGES['general'],
                reply_markup=InlineKeyboards.error_keyboard('general')
            )

    async def handle_confirm_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle confirm delete callback"""
        try:
            user_id = update.effective_user.id

            # Delete user email
            success = await self.mongo_client.deactivate_user(user_id)

            if success:
                await update.callback_query.edit_message_text(
                    SUCCESS_MESSAGES['email_deleted'],
                    reply_markup=InlineKeyboards.single_button_keyboard(
                        "✉️ Create New Email", "new_email"
                    )
                )
            else:
                await update.callback_query.edit_message_text(
                    "❌ Failed to delete email. Please try again.",
                    reply_markup=InlineKeyboards.error_keyboard('general')
                )

        except Exception as e:
            logger.error(f"Error in handle_confirm_delete: {e}")
            await update.callback_query.edit_message_text(
                ERROR_MESSAGES['general'],
                reply_markup=InlineKeyboards.error_keyboard('general')
            )

    async def handle_cancel_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle cancel action callback"""
        try:
            user_id = update.effective_user.id

            # Check user state and show appropriate message
            user_data = await self.mongo_client.get_user(user_id)

            if user_data:
                email = user_data.get('email')
                await update.callback_query.edit_message_text(
                    f"✅ Action cancelled.\n\n"
                    f"📧 Your email: <code>{email}</code>",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboards.main_actions_keyboard()
                )
            else:
                await update.callback_query.edit_message_text(
                    "✅ Action cancelled.\n\n"
                    "Create a new email to get started!",
                    reply_markup=InlineKeyboards.single_button_keyboard(
                        "✉️ Create Email", "new_email"
                    )
                )

        except Exception as e:
            logger.error(f"Error in handle_cancel_action: {e}")
            await update.callback_query.edit_message_text(
                "✅ Action cancelled",
                reply_markup=InlineKeyboards.main_actions_keyboard()
            )

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle help callback"""
        try:
            from handlers.command_handlers import CommandHandlers

            # Create temporary command handlers instance to reuse help logic
            command_handlers = CommandHandlers(self.mongo_client)
            await command_handlers.help_command(update, context)

        except Exception as e:
            logger.error(f"Error in handle_help: {e}")
            await update.callback_query.edit_message_text(
                "📖 Help temporarily unavailable.",
                reply_markup=InlineKeyboards.main_actions_keyboard()
            )

    async def handle_copy_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle copy email callback"""
        try:
            callback_data = update.callback_query.data
            email = callback_data.split(":", 1)[1]

            await update.callback_query.answer(
                f"📋 Email copied to clipboard:\n{email}",
                show_alert=True
            )

        except Exception as e:
            logger.error(f"Error in handle_copy_email: {e}")
            await update.callback_query.answer("❌ Failed to copy email", show_alert=True)

    async def handle_share_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle share email callback"""
        try:
            callback_data = update.callback_query.data
            email = callback_data.split(":", 1)[1]

            # Create shareable text
            share_text = f"📧 My temporary email: {email}"

            # Note: Telegram doesn't have a native share function for bots
            # We'll copy it to clipboard instead
            await update.callback_query.answer(
                f"📤 Share this email:\n\n{share_text}",
                show_alert=True
            )

        except Exception as e:
            logger.error(f"Error in handle_share_email: {e}")
            await update.callback_query.answer("❌ Failed to prepare share", show_alert=True)

    async def handle_loading_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle loading callbacks (should not happen in normal flow)"""
        await update.callback_query.answer("⏳ Processing...", show_alert=False)

    async def handle_unknown_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown callbacks"""
        try:
            await update.callback_query.answer("❓ Unknown action", show_alert=True)
            await update.callback_query.edit_message_text(
                "❓ This action is not available.",
                reply_markup=InlineKeyboards.main_actions_keyboard()
            )

        except Exception as e:
            logger.error(f"Error in handle_unknown_callback: {e}")

    async def _display_inbox_callback(self, update: Update, messages: list, email: str):
        """
        Display inbox messages for callback handler
        """
        try:
            if not messages:
                await update.callback_query.edit_message_text(
                    f"📭 Your inbox is empty.\n\n"
                    f"📧 Email: <code>{email}</code>",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboards.empty_state_keyboard()
                )
                return

            # Update the original message with inbox header
            header_text = f"📥 <b>Your Inbox ({len(messages)} messages)</b>\n\n"
            header_text += f"📧 <code>{email}</code>\n\n"
            header_text += "💡 Use buttons below to view messages"

            await update.callback_query.edit_message_text(
                header_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboards.email_list_keyboard(messages)
            )

        except Exception as e:
            logger.error(f"Error displaying inbox callback: {e}")
            raise