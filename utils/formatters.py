"""
Message formatting utilities for Telegram Temp Mail Bot
Provides formatting functions for various types of messages and data
"""

import html
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from config import (
    MAX_INBOX_MESSAGES,
    SUCCESS_MESSAGES,
    ERROR_MESSAGES
)

logger = logging.getLogger(__name__)


class Formatters:
    """Utility class for message formatting"""

    @staticmethod
    def format_welcome_message(user_data: Dict[str, Any]) -> str:
        """
        Format welcome message for user
        Returns formatted welcome message
        """
        try:
            user_name = user_data.get('first_name', 'User')
            username = user_data.get('username', '')

            if username:
                user_display = f"{user_name} (@{username})"
            else:
                user_display = user_name

            message = [
                f"🎉 Welcome, {html.escape(user_display)}!",
                "",
                "📧 <b>Telegram Temp Mail Bot</b>",
                "",
                "I'll help you create temporary email addresses that forward to this chat.",
                "",
                "✨ <b>Features:</b>",
                "• 📧 Receive emails instantly",
                "• 📎 Download attachments",
                "• ⏰ Auto-expiring emails",
                "• 🔄 Real-time updates",
                "",
                "👇 Use the buttons below to get started!"
            ]

            return "\n".join(message)

        except Exception as e:
            logger.error(f"Error formatting welcome message: {e}")
            return "🎉 Welcome to Temp Mail Bot!"

    @staticmethod
    def format_email_created_message(email: str, expiry_hours: int = 1) -> str:
        """
        Format email creation success message
        Returns formatted email creation message
        """
        try:
            message = [
                f"✅ {SUCCESS_MESSAGES['email_created']}",
                "",
                f"📧 Your temporary email:",
                f"<code>{html.escape(email)}</code>",
                "",
                f"⏰ Valid for {expiry_hours} hour{'s' if expiry_hours != 1 else ''}",
                "📥 Ready to receive emails!",
                "",
                "💡 Send emails to this address and they'll appear here automatically."
            ]

            return "\n".join(message)

        except Exception as e:
            logger.error(f"Error formatting email created message: {e}")
            return f"✅ Email created: {email}"

    @staticmethod
    def format_inbox_header(email: str, message_count: int, new_count: int = 0) -> str:
        """
        Format inbox header message
        Returns formatted inbox header
        """
        try:
            header_lines = [
                f"📥 <b>Your Inbox</b>",
                ""
            ]

            if message_count > 0:
                if new_count > 0:
                    header_lines.append(f"📧 <code>{html.escape(email)}</code>")
                    header_lines.append(f"📬 {message_count} messages ({new_count} new)")
                else:
                    header_lines.append(f"📧 <code>{html.escape(email)}</code>")
                    header_lines.append(f"📬 {message_count} messages")
            else:
                header_lines.append(f"📧 <code>{html.escape(email)}</code>")
                header_lines.append("📭 No messages yet")

            header_lines.extend([
                "",
                "💡 Messages below are previews. Tap to view full content."
            ])

            return "\n".join(header_lines)

        except Exception as e:
            logger.error(f"Error formatting inbox header: {e}")
            return f"📥 Inbox for {email}"

    @staticmethod
    def format_message_preview(message_data: Dict[str, Any], index: int = None) -> str:
        """
        Format individual message preview
        Returns formatted message preview
        """
        try:
            sender = message_data.get('sender', 'Unknown')
            subject = message_data.get('subject', 'No Subject')
            body_text = message_data.get('body_text', '')
            has_attachments = message_data.get('has_attachments', False)
            attachment_count = message_data.get('attachment_count', 0)
            date = message_data.get('date', datetime.utcnow())

            # Format index if provided
            prefix = f"{index}. " if index else ""

            # Extract sender display name
            sender_display = sender.split('<')[0].strip() if '<' in sender else sender
            sender_display = sender_display.strip('"\'') or sender

            # Truncate subject if too long
            if len(subject) > 40:
                subject = subject[:37] + "..."

            # Create preview text
            preview_lines = [
                f"{prefix}📧 <b>{html.escape(sender_display[:30])}</b>",
                f"📋 {html.escape(subject)}",
                f"⏰ {Formatters.format_relative_time(date)}",
            ]

            # Add preview of body text
            if body_text:
                preview_text = Formatters.create_text_preview(body_text, 100)
                preview_lines.append(f"📄 {preview_text}")

            # Add attachment indicator
            if has_attachments:
                if attachment_count == 1:
                    preview_lines.append("📎 1 attachment")
                else:
                    preview_lines.append(f"📎 {attachment_count} attachments")

            return "\n".join(preview_lines)

        except Exception as e:
            logger.error(f"Error formatting message preview: {e}")
            return "❌ Error formatting message"

    @staticmethod
    def format_full_message(message_data: Dict[str, Any]) -> str:
        """
        Format full email message for display
        Returns formatted full message
        """
        try:
            sender = message_data.get('sender', 'Unknown')
            to = message_data.get('to', 'Unknown')
            subject = message_data.get('subject', 'No Subject')
            date_str = message_data.get('date_str', '')
            body_text = message_data.get('body_text', '')
            attachments = message_data.get('attachments', [])

            # Build message
            message_lines = [
                "📧 <b>Full Email Message</b>",
                "",
                f"<b>From:</b> {html.escape(sender)}",
                f"<b>To:</b> {html.escape(to)}",
                f"<b>Subject:</b> {html.escape(subject)}",
                f"<b>Date:</b> {html.escape(date_str)}",
                "",
                "─" * 20,
                ""
            ]

            # Add body content
            if body_text:
                # Clean and escape body text
                clean_body = Formatters.clean_message_body(body_text)
                message_lines.append(clean_body)
            else:
                message_lines.append("<i>No message content</i>")

            # Add attachment information
            if attachments:
                message_lines.extend([
                    "",
                    "─" * 20,
                    "",
                    Formatters.format_attachment_list(attachments)
                ])

            return "\n".join(message_lines)

        except Exception as e:
            logger.error(f"Error formatting full message: {e}")
            return "❌ Error formatting message"

    @staticmethod
    def format_attachment_list(attachments: List[Dict[str, Any]]) -> str:
        """
        Format attachment list for display
        Returns formatted attachment list
        """
        try:
            if not attachments:
                return "No attachments"

            lines = ["📎 <b>Attachments:</b>"]

            for i, attachment in enumerate(attachments, 1):
                filename = attachment.get('filename', 'unknown')
                size = attachment.get('size', 0)
                content_type = attachment.get('content_type', 'application/octet-stream')

                # Format file size
                size_str = Formatters.format_file_size(size)

                # Get file icon
                icon = Formatters.get_file_icon(content_type, filename)

                lines.append(f"{i}. {icon} <code>{html.escape(filename)}</code> ({size_str})")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Error formatting attachment list: {e}")
            return "📎 Attachments (error loading details)"

    @staticmethod
    def format_error_message(error_type: str, additional_info: str = None) -> str:
        """
        Format error message for display
        Returns formatted error message
        """
        try:
            base_message = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES['general'])

            lines = [
                "❌ <b>Error</b>",
                "",
                base_message
            ]

            if additional_info:
                lines.extend([
                    "",
                    f"<i>{html.escape(additional_info)}</i>"
                ])

            lines.extend([
                "",
                "💡 Try again or use /help for assistance."
            ])

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Error formatting error message: {e}")
            return "❌ An error occurred. Please try again."

    @staticmethod
    def format_user_statistics(stats: Dict[str, Any]) -> str:
        """
        Format user statistics for display
        Returns formatted statistics message
        """
        try:
            email = stats.get('email', 'Unknown')
            created_at = stats.get('created_at')
            expires_at = stats.get('expires_at')
            time_remaining = stats.get('time_remaining')
            message_count = stats.get('message_count', 0)
            total_messages = stats.get('total_messages_received', 0)
            is_active = stats.get('is_active', False)

            lines = [
                "📊 <b>Your Statistics</b>",
                "",
                f"📧 Email: <code>{html.escape(email)}</code>"
            ]

            # Add status information
            if is_active and time_remaining:
                hours = int(time_remaining.total_seconds() // 3600)
                minutes = int((time_remaining.total_seconds() % 3600) // 60)
                lines.append(f"⏰ Expires in: {hours}h {minutes}m")
            elif is_active:
                lines.append("✅ Active (expiry time unknown)")
            else:
                lines.append("❌ Expired")

            # Add creation date
            if created_at:
                lines.append(f"📅 Created: {created_at.strftime('%Y-%m-%d %H:%M')}")

            # Add message counts
            lines.extend([
                f"📬 Current messages: {message_count}",
                f"📨 Total received: {total_messages}"
            ])

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Error formatting user statistics: {e}")
            return "📊 Statistics temporarily unavailable"

    @staticmethod
    def format_help_message() -> str:
        """
        Format help message
        Returns formatted help message
        """
        try:
            lines = [
                "📖 <b>Temp Mail Bot Help</b>",
                "",
                "<b>📧 Commands:</b>",
                "/start - Start bot and get email",
                "/new - Create new temp email",
                "/inbox - Check your inbox",
                "/refresh - Refresh inbox",
                "/delete - Delete temp email",
                "/help - Show this help",
                "/status - Show email status",
                "",
                "<b>🎯 Features:</b>",
                "• Receive emails instantly",
                "• Download all attachments",
                "• Auto-expiring addresses (1 hour)",
                "• Real-time email updates",
                "• Secure IMAP connection",
                "",
                "<b>🔘 Buttons:</b>",
                "• 📥 Inbox - Check emails",
                "• ✉️ New Email - Create address",
                "• 🔁 Refresh - Check for new emails",
                "• 🗑️ Delete - Remove temp email",
                "",
                "<b>💡 How it works:</b>",
                "1. Create a temporary email address",
                "2. Use it anywhere you need",
                "3. Emails appear in the bot automatically",
                "4. Download attachments directly",
                "5. Email expires after 1 hour",
                "",
                "<b>🔒 Privacy:</b>",
                "• Emails are temporary and auto-deleted",
                "• No permanent storage of email content",
                "• Secure IMAP connection",
                "",
                "Need help? Contact support!"
            ]

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Error formatting help message: {e}")
            return "📖 Help temporarily unavailable"

    @staticmethod
    def format_confirmation_message(action: str, item_description: str) -> str:
        """
        Format confirmation message for actions
        Returns formatted confirmation message
        """
        try:
            action_emoji = {
                'delete': '🗑️',
                'clear': '🧹',
                'reset': '🔄'
            }.get(action, '⚠️')

            lines = [
                f"{action_emoji} <b>Confirm Action</b>",
                "",
                f"Are you sure you want to {action}?",
                ""
            ]

            if item_description:
                lines.append(f"📋 <b>{html.escape(item_description)}</b>")
                lines.append("")

            lines.extend([
                "⚠️ This action cannot be undone!",
                "",
                "Choose an option below:"
            ])

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Error formatting confirmation message: {e}")
            return f"⚠️ Confirm {action}?"

    @staticmethod
    def create_text_preview(text: str, max_length: int = 200) -> str:
        """
        Create a preview of text content
        Returns preview text
        """
        try:
            if not text:
                return "No content"

            # Clean up the text
            text = text.strip()
            text = ' '.join(text.split())  # Remove extra whitespace

            # Remove common email signatures and quoted text
            lines = text.split('\n')
            clean_lines = []
            skip_patterns = [
                r'^--\s*$',  # Email signature separator
                r'^>.*',    # Quoted text
                r'^On .* wrote:',  # Quoted text introduction
                r'^Sent from my.*',  # Mobile signatures
                r'^Best regards',
                r'^Regards',
                r'^Sincerely',
                r'^Thank you',
                r'^Thanks',
            ]

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Skip if matches any pattern
                if any(re.match(pattern, line, re.IGNORECASE) for pattern in skip_patterns):
                    continue

                clean_lines.append(line)

                # Stop if we have enough content
                if len('\n'.join(clean_lines)) > max_length:
                    break

            preview_text = '\n'.join(clean_lines)

            # Truncate if still too long
            if len(preview_text) > max_length:
                preview_text = preview_text[:max_length-3] + "..."

            return preview_text

        except Exception as e:
            logger.error(f"Error creating text preview: {e}")
            return "Preview error"

    @staticmethod
    def format_relative_time(date: datetime) -> str:
        """
        Format relative time (e.g., "2 hours ago")
        Returns formatted relative time
        """
        try:
            now = datetime.utcnow()
            diff = now - date

            if diff.total_seconds() < 30:
                return "just now"
            elif diff.total_seconds() < 60:
                return "less than a minute ago"
            elif diff.total_seconds() < 3600:
                minutes = int(diff.total_seconds() / 60)
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif diff.total_seconds() < 86400:
                hours = int(diff.total_seconds() / 3600)
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                days = diff.days
                return f"{days} day{'s' if days != 1 else ''} ago"

        except Exception as e:
            logger.error(f"Error formatting relative time: {e}")
            return "unknown time"

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human readable format
        Returns formatted file size
        """
        try:
            if size_bytes == 0:
                return "0 B"

            size_names = ["B", "KB", "MB", "GB"]
            i = 0
            size = float(size_bytes)

            while size >= 1024.0 and i < len(size_names) - 1:
                size /= 1024.0
                i += 1

            return f"{size:.1f} {size_names[i]}"

        except Exception as e:
            logger.error(f"Error formatting file size: {e}")
            return f"{size_bytes} B"

    @staticmethod
    def get_file_icon(content_type: str, filename: str) -> str:
        """
        Get appropriate icon for file type
        Returns emoji icon
        """
        try:
            content_type = content_type.lower()
            filename_lower = filename.lower() if filename else ""

            # Images
            if (content_type.startswith('image/') or
                any(filename_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'])):
                return "🖼️"

            # PDF
            elif content_type == 'application/pdf' or filename_lower.endswith('.pdf'):
                return "📄"

            # Documents
            elif (content_type.startswith('text/') or
                  any(filename_lower.endswith(ext) for ext in ['.doc', '.docx', '.txt', '.rtf', '.odt'])):
                return "📝"

            # Spreadsheets
            elif (content_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'] or
                  any(filename_lower.endswith(ext) for ext in ['.xls', '.xlsx', '.csv'])):
                return "📊"

            # Archives
            elif (content_type in ['application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed'] or
                  any(filename_lower.endswith(ext) for ext in ['.zip', '.rar', '.7z', '.tar', '.gz'])):
                return "📦"

            # Audio
            elif content_type.startswith('audio/'):
                return "🎵"

            # Video
            elif content_type.startswith('video/'):
                return "🎥"

            # Default
            else:
                return "📎"

        except Exception as e:
            logger.error(f"Error getting file icon: {e}")
            return "📎"

    @staticmethod
    def clean_message_body(body: str) -> str:
        """
        Clean message body for safe display
        Returns cleaned body text
        """
        try:
            if not body:
                return ""

            # Escape HTML
            body = html.escape(body)

            # Basic formatting
            body = body.replace('\n', '\n')

            # Clean up extra whitespace
            body = '\n'.join(line.strip() for line in body.split('\n') if line.strip())

            return body

        except Exception as e:
            logger.error(f"Error cleaning message body: {e}")
            return html.escape(body) if body else ""

    @staticmethod
    def format_loading_message(action: str) -> str:
        """
        Format loading message for actions
        Returns formatted loading message
        """
        try:
            loading_messages = {
                'new_email': "⏳ Creating your temporary email...",
                'inbox': "🔄 Checking your inbox...",
                'refresh': "🔄 Refreshing emails...",
                'delete': "🗑️ Deleting your email...",
                'view_message': "📧 Loading message...",
                'attachments': "📎 Preparing attachments..."
            }

            return loading_messages.get(action, "⏳ Loading...")

        except Exception as e:
            logger.error(f"Error formatting loading message: {e}")
            return "⏳ Loading..."

    @staticmethod
    def truncate_message(message: str, max_length: int = 4000) -> str:
        """
        Truncate message to fit Telegram limits
        Returns truncated message
        """
        try:
            if len(message) <= max_length:
                return message

            # Find a good breaking point
            truncated = message[:max_length-20]  # Leave room for continuation notice

            # Try to break at a sentence or newline
            for break_char in ['\n\n', '. ', '!\n', '?\n']:
                last_break = truncated.rfind(break_char)
                if last_break > max_length // 2:  # Don't break too early
                    truncated = truncated[:last_break + len(break_char)]
                    break

            return truncated + "\n\n<i>... Message truncated</i>"

        except Exception as e:
            logger.error(f"Error truncating message: {e}")
            return message[:max_length] if len(message) > max_length else message