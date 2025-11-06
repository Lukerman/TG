"""
Email parser and attachment handler for Telegram Temp Mail Bot
Handles email content parsing, formatting, and attachment processing
"""

import logging
import re
import html
import os
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse

import magic

from config import (
    IMAGE_EXTENSIONS,
    DOCUMENT_EXTENSIONS,
    ARCHIVE_EXTENSIONS,
    MAX_ATTACHMENT_SIZE,
    TEMP_FILE_DIR,
    MAX_TEMP_FILE_AGE,
    SANITIZE_EMAIL_CONTENT,
    ALLOWED_HTML_TAGS,
    BLOCKED_PATTERNS
)

logger = logging.getLogger(__name__)


class EmailParser:
    """Email content parser and attachment handler"""

    def __init__(self):
        self.temp_files = []  # Track temporary files for cleanup

    def format_message_preview(self, message_data: Dict[str, Any], preview_length: int = 200) -> str:
        """
        Format message for preview in inbox list
        Returns formatted preview string
        """
        try:
            # Extract message data
            sender = message_data.get('sender', 'Unknown')
            subject = message_data.get('subject', 'No Subject')
            body_text = message_data.get('body_text', '')
            has_attachments = message_data.get('has_attachments', False)
            attachment_count = message_data.get('attachment_count', 0)
            received_date = message_data.get('date', datetime.utcnow())

            # Format sender name
            sender_name = self._extract_display_name(sender)
            if not sender_name:
                sender_name = sender.split('@')[0] if '@' in sender else sender

            # Truncate subject if too long
            if len(subject) > 50:
                subject = subject[:47] + "..."

            # Create preview from body text
            preview = self._create_text_preview(body_text, preview_length)

            # Format relative time
            time_ago = self._format_relative_time(received_date)

            # Build preview message
            preview_lines = [
                f"📧 <b>{html.escape(sender_name)}</b>",
                f"📋 {html.escape(subject)}",
                f"⏰ {time_ago}",
                "",
                f"📄 {preview}"
            ]

            # Add attachment info
            if has_attachments:
                if attachment_count == 1:
                    preview_lines.append("📎 1 attachment")
                else:
                    preview_lines.append(f"📎 {attachment_count} attachments")

            return "\n".join(preview_lines)

        except Exception as e:
            logger.error(f"Error formatting message preview: {e}")
            return "❌ Error formatting message preview"

    def format_full_message(self, message_data: Dict[str, Any]) -> str:
        """
        Format full message for display
        Returns formatted full message string
        """
        try:
            # Extract message data
            sender = message_data.get('sender', 'Unknown')
            to = message_data.get('to', 'Unknown')
            subject = message_data.get('subject', 'No Subject')
            date_str = message_data.get('date_str', '')
            body_text = message_data.get('body_text', '')
            body_html = message_data.get('body_html', '')
            attachments = message_data.get('attachments', [])
            message_id = message_data.get('message_id', '')

            # Sanitize content if enabled
            if SANITIZE_EMAIL_CONTENT:
                body_text = self._sanitize_content(body_text)
                subject = self._sanitize_content(subject)
                sender = self._sanitize_content(sender)

            # Build message header
            header_lines = [
                "📧 <b>Full Email Message</b>",
                "",
                f"<b>From:</b> {html.escape(sender)}",
                f"<b>To:</b> {html.escape(to)}",
                f"<b>Subject:</b> {html.escape(subject)}",
                f"<b>Date:</b> {html.escape(date_str)}",
            ]

            # Add message ID if available
            if message_id:
                header_lines.append(f"<b>Message ID:</b> <code>{html.escape(message_id)}</code>")

            header_lines.append("")

            # Process body content
            body_content = ""

            # Prefer HTML content if available and cleanable
            if body_html:
                body_content = self._clean_html_content(body_html)
            else:
                body_content = html.escape(body_text)

            # Limit message length for Telegram
            max_length = 3500  # Leave room for header and attachments
            if len(body_content) > max_length:
                body_content = body_content[:max_length] + "\n\n<i>... Message truncated</i>"

            full_message = "\n".join(header_lines) + body_content

            # Add attachment information
            if attachments:
                full_message += "\n\n" + self._format_attachment_list(attachments)

            return full_message

        except Exception as e:
            logger.error(f"Error formatting full message: {e}")
            return f"❌ Error formatting message: {str(e)}"

    def _create_text_preview(self, text: str, max_length: int) -> str:
        """
        Create preview text from message body
        Returns preview string
        """
        if not text:
            return "No content"

        # Clean up the text
        text = re.sub(r'\s+', ' ', text.strip())

        # Remove common email signatures and quoted text
        lines = text.split('\n')
        clean_lines = []
        skip_patterns = [
            r'^--\s*$',  # Email signature separator
            r'^>.*',    # Quoted text
            r'^On .* wrote:',  # Quoted text introduction
            r'^Sent from my.*',  # Mobile signatures
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

    def _extract_display_name(self, sender: str) -> str:
        """
        Extract display name from sender string
        Returns display name or empty string
        """
        if not sender:
            return ""

        # Handle format: "Name <email@domain.com>"
        if '<' in sender and '>' in sender:
            name_part = sender.split('<')[0].strip()
            if name_part:
                # Remove quotes if present
                name_part = name_part.strip('"\'')
                return name_part

        # Handle format: "email@domain.com"
        if '@' in sender:
            return sender.split('@')[0]

        return sender

    def _format_relative_time(self, date: datetime) -> str:
        """
        Format relative time (e.g., "2 hours ago")
        Returns formatted relative time string
        """
        try:
            now = datetime.utcnow()
            diff = now - date

            if diff.total_seconds() < 60:
                return "just now"
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
            logger.warning(f"Error formatting relative time: {e}")
            return "unknown time"

    def _format_attachment_list(self, attachments: List[Dict[str, Any]]) -> str:
        """
        Format attachment list for display
        Returns formatted attachment information
        """
        if not attachments:
            return ""

        lines = ["📎 <b>Attachments:</b>"]

        for i, attachment in enumerate(attachments, 1):
            filename = attachment.get('filename', 'unknown')
            size = attachment.get('size', 0)
            content_type = attachment.get('content_type', 'unknown')

            # Format file size
            size_str = self._format_file_size(size)

            # Get file icon
            icon = self._get_file_icon(content_type, filename)

            lines.append(f"{i}. {icon} <code>{html.escape(filename)}</code> ({size_str})")

        return "\n".join(lines)

    def _format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human readable format
        Returns formatted size string
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

        except Exception:
            return f"{size_bytes} B"

    def _get_file_icon(self, content_type: str, filename: str) -> str:
        """
        Get appropriate icon for file type
        Returns emoji icon
        """
        content_type = content_type.lower()
        filename_lower = filename.lower() if filename else ""

        # Images
        if content_type.startswith('image/') or any(filename_lower.endswith(ext) for ext in IMAGE_EXTENSIONS):
            return "🖼️"

        # PDF
        elif content_type == 'application/pdf' or filename_lower.endswith('.pdf'):
            return "📄"

        # Documents
        elif any(filename_lower.endswith(ext) for ext in DOCUMENT_EXTENSIONS):
            return "📝"

        # Archives
        elif any(filename_lower.endswith(ext) for ext in ARCHIVE_EXTENSIONS):
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

    def _sanitize_content(self, content: str) -> str:
        """
        Sanitize email content for safe display
        Returns sanitized content
        """
        if not content:
            return content

        try:
            # Remove potentially dangerous patterns
            for pattern in BLOCKED_PATTERNS:
                content = re.sub(pattern, '', content, flags=re.IGNORECASE)

            # Remove or replace potentially dangerous HTML
            content = html.escape(content)

            return content

        except Exception as e:
            logger.warning(f"Error sanitizing content: {e}")
            return content

    def _clean_html_content(self, html_content: str) -> str:
        """
        Clean HTML content for safe display in Telegram
        Returns cleaned HTML string
        """
        try:
            if not html_content:
                return ""

            # Basic HTML cleaning
            content = html_content.strip()

            # Remove dangerous tags and attributes
            dangerous_tags = ['script', 'style', 'iframe', 'object', 'embed', 'form', 'input']
            for tag in dangerous_tags:
                content = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', content, flags=re.IGNORECASE | re.DOTALL)
                content = re.sub(f'<{tag}[^>]*/>', '', content, flags=re.IGNORECASE)

            # Remove style attributes and event handlers
            content = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)
            content = re.sub(r'\s+style\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)

            # Convert to basic HTML that Telegram supports
            # Telegram supports: b, i, u, strong, em, a, br, p
            content = re.sub(r'<(?!(?:b|i|u|strong|em|a|br|p)(?:\s|>))/?[^>]*>', '', content, flags=re.IGNORECASE)

            # Clean up whitespace
            content = re.sub(r'\s+', ' ', content)

            return content.strip()

        except Exception as e:
            logger.warning(f"Error cleaning HTML content: {e}")
            return html.escape(html_content)

    async def prepare_attachment_for_telegram(self, attachment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Prepare attachment for sending via Telegram
        Returns attachment data ready for Telegram or None if failed
        """
        try:
            filename = attachment.get('filename', 'attachment')
            content_type = attachment.get('content_type', 'application/octet-stream')
            data = attachment.get('data', b'')
            size = attachment.get('size', len(data))

            # Check size limits
            if MAX_ATTACHMENT_SIZE and size > MAX_ATTACHMENT_SIZE:
                logger.warning(f"Attachment {filename} too large: {size} bytes")
                return None

            # Create temporary file
            temp_dir = TEMP_FILE_DIR if os.path.exists(TEMP_FILE_DIR) else tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"temp_{int(datetime.utcnow().timestamp())}_{filename}")

            try:
                # Write attachment to temporary file
                with open(temp_path, 'wb') as f:
                    f.write(data)

                # Track temporary file for cleanup
                self.temp_files.append({
                    'path': temp_path,
                    'created_at': datetime.utcnow()
                })

                # Determine MIME type
                mime_type = self._get_mime_type(temp_path, content_type)

                return {
                    'path': temp_path,
                    'filename': filename,
                    'mime_type': mime_type,
                    'size': size,
                    'is_image': mime_type.startswith('image/'),
                    'is_document': True
                }

            except Exception as e:
                logger.error(f"Error creating temporary file for {filename}: {e}")
                # Clean up if file creation failed
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return None

        except Exception as e:
            logger.error(f"Error preparing attachment {attachment.get('filename', 'unknown')}: {e}")
            return None

    def _get_mime_type(self, file_path: str, fallback_mime: str) -> str:
        """
        Get MIME type of file
        Returns MIME type string
        """
        try:
            mime = magic.Magic(mime=True)
            detected_mime = mime.from_file(file_path)

            # Validate detected MIME type
            if detected_mime and '/' in detected_mime:
                return detected_mime

            return fallback_mime

        except Exception as e:
            logger.debug(f"Error detecting MIME type for {file_path}: {e}")
            return fallback_mime

    async def cleanup_temp_files(self) -> int:
        """
        Clean up old temporary files
        Returns number of files cleaned up
        """
        cleaned_count = 0

        try:
            now = datetime.utcnow()
            files_to_remove = []

            for temp_file in self.temp_files:
                created_at = temp_file.get('created_at', now)
                age = now - created_at

                if age.total_seconds() > MAX_TEMP_FILE_AGE:
                    files_to_remove.append(temp_file)

            for temp_file in files_to_remove:
                try:
                    file_path = temp_file.get('path')
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                        logger.debug(f"Cleaned up temporary file: {file_path}")

                    # Remove from tracking
                    self.temp_files.remove(temp_file)
                    cleaned_count += 1

                except Exception as e:
                    logger.warning(f"Error removing temporary file {temp_file.get('path')}: {e}")

        except Exception as e:
            logger.error(f"Error during temp file cleanup: {e}")

        return cleaned_count

    def get_attachment_summary(self, attachments: List[Dict[str, Any]]) -> str:
        """
        Get summary of attachments for quick display
        Returns attachment summary string
        """
        if not attachments:
            return "No attachments"

        total_count = len(attachments)
        total_size = sum(att.get('size', 0) for att in attachments)

        # Count by type
        images = sum(1 for att in attachments if att.get('content_type', '').startswith('image/'))
        documents = total_count - images

        summary_parts = []

        if total_count == 1:
            summary_parts.append("1 attachment")
        else:
            summary_parts.append(f"{total_count} attachments")

        if images > 0:
            summary_parts.append(f"{images} image{'s' if images != 1 else ''}")

        if documents > 0:
            summary_parts.append(f"{documents} document{'s' if documents != 1 else ''}")

        if total_size > 0:
            size_str = self._format_file_size(total_size)
            summary_parts.append(f"({size_str})")

        return " • ".join(summary_parts)

    def is_safe_filename(self, filename: str) -> bool:
        """
        Check if filename is safe for use
        Returns True if safe, False otherwise
        """
        if not filename:
            return False

        # Check for dangerous patterns
        dangerous_patterns = [
            r'\.exe$', r'\.bat$', r'\.cmd$', r'\.com$', r'\.pif$',
            r'\.scr$', r'\.vbs$', r'\.js$', r'\.jar$', r'\.php$',
            r'\..*',  # Hidden files
        ]

        filename_lower = filename.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, filename_lower):
                return False

        # Check for dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        for char in dangerous_chars:
            if char in filename:
                return False

        # Check length
        if len(filename) > 255:
            return False

        return True