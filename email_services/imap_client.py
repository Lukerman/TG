"""
IMAP client for Telegram Temp Mail Bot
Handles email fetching and IMAP server operations
"""

import asyncio
import email
import imaplib
import ssl
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from email.header import decode_header

from config import (
    IMAP_HOST,
    IMAP_PORT,
    IMAP_USERNAME,
    IMAP_PASSWORD,
    IMAP_USE_SSL,
    IMAP_CONNECTION_TIMEOUT,
    IMAP_READ_TIMEOUT,
    IMAP_MAX_RETRIES,
    IMAP_RETRY_DELAY,
    MAX_INBOX_MESSAGES
)

logger = logging.getLogger(__name__)


class IMAPClient:
    """IMAP client for email operations"""

    def __init__(self):
        self.connection = None
        self.connected = False
        self.selected_folder = None
        self.connection_time = None

    async def connect(self) -> bool:
        """
        Connect to IMAP server
        Returns True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to IMAP server {IMAP_HOST}:{IMAP_PORT}")

            # Create IMAP connection
            if IMAP_USE_SSL:
                self.connection = imaplib.IMAP4_SSL(
                    host=IMAP_HOST,
                    port=IMAP_PORT,
                    timeout=IMAP_CONNECTION_TIMEOUT
                )
            else:
                self.connection = imaplib.IMAP4(
                    host=IMAP_HOST,
                    port=IMAP_PORT,
                    timeout=IMAP_CONNECTION_TIMEOUT
                )

            # Login to server
            try:
                self.connection.login(IMAP_USERNAME, IMAP_PASSWORD)
                logger.info("Successfully logged into IMAP server")
            except imaplib.IMAP4.error as e:
                logger.error(f"IMAP login failed: {e}")
                return False

            self.connected = True
            self.connection_time = datetime.utcnow()
            logger.info("IMAP connection established successfully")
            return True

        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP connection error: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to IMAP: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect from IMAP server"""
        try:
            if self.connection and self.connected:
                # Close selected folder if any
                if self.selected_folder:
                    self.connection.close()
                    self.selected_folder = None

                # Logout from server
                self.connection.logout()
                logger.info("Logged out from IMAP server")

        except imaplib.IMAP4.error as e:
            logger.warning(f"Error during IMAP logout: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error during IMAP disconnect: {e}")
        finally:
            self.connected = False
            self.connection = None
            self.connection_time = None

    async def select_folder(self, folder_name: str = "INBOX") -> bool:
        """
        Select IMAP folder
        Returns True if successful, False otherwise
        """
        if not self.connected or not self.connection:
            logger.error("Not connected to IMAP server")
            return False

        try:
            # Close current folder if one is selected
            if self.selected_folder:
                self.connection.close()

            # Select new folder
            status, data = self.connection.select(folder_name)
            if status == "OK":
                self.selected_folder = folder_name
                logger.info(f"Selected IMAP folder: {folder_name}")
                return True
            else:
                logger.error(f"Failed to select folder {folder_name}: {data}")
                return False

        except imaplib.IMAP4.error as e:
            logger.error(f"Error selecting folder {folder_name}: {e}")
            return False

    async def search_emails(self, recipient_email: str, since_date: Optional[datetime] = None) -> List[str]:
        """
        Search for emails to a specific recipient
        Returns list of email UIDs
        """
        if not self.connected or not self.connection:
            logger.error("Not connected to IMAP server")
            return []

        # Ensure INBOX is selected
        if not await self.select_folder("INBOX"):
            return []

        try:
            # Build search criteria
            search_criteria = [f'(TO "{recipient_email}")']

            # Add date filter if provided
            if since_date:
                date_str = since_date.strftime("%d-%b-%Y")
                search_criteria.append(f'(SINCE {date_str})')

            search_query = ' '.join(search_criteria)
            logger.debug(f"IMAP search query: {search_query}")

            # Perform search
            status, data = self.connection.uid('search', None, search_query)

            if status != "OK":
                logger.error(f"IMAP search failed: {data}")
                return []

            # Parse UIDs from response
            if data[0]:
                uids = data[0].decode().split()
                logger.debug(f"Found {len(uids)} emails for {recipient_email}")
                return uids
            else:
                logger.debug(f"No emails found for {recipient_email}")
                return []

        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP search error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during IMAP search: {e}")
            return []

    async def fetch_message(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        Fetch full message by UID
        Returns message data dictionary or None if failed
        """
        if not self.connected or not self.connection:
            logger.error("Not connected to IMAP server")
            return None

        try:
            # Fetch message body
            status, data = self.connection.uid('fetch', uid, '(RFC822)')

            if status != "OK":
                logger.error(f"Failed to fetch message {uid}: {data}")
                return None

            if not data or not data[0]:
                logger.error(f"No data received for message {uid}")
                return None

            # Parse email message
            raw_email = data[0][1]
            if isinstance(raw_email, bytes):
                raw_email = raw_email.decode('utf-8', errors='ignore')

            email_message = email.message_from_string(raw_email)

            # Extract email information
            message_data = await self._parse_email_message(email_message, uid)

            return message_data

        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP fetch error for message {uid}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching message {uid}: {e}")
            return None

    async def fetch_message_list(self, recipient_email: str, limit: int = MAX_INBOX_MESSAGES,
                                 since_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Fetch list of messages for recipient
        Returns list of message data
        """
        try:
            # Search for emails
            uids = await self.search_emails(recipient_email, since_date)

            if not uids:
                return []

            # Get most recent emails (reverse order)
            uids = uids[-limit:] if len(uids) > limit else uids

            messages = []
            for uid in reversed(uids):  # Get newest first
                try:
                    message_data = await self.fetch_message(uid)
                    if message_data:
                        messages.append(message_data)
                except Exception as e:
                    logger.warning(f"Failed to fetch message {uid}: {e}")
                    continue

            return messages

        except Exception as e:
            logger.error(f"Error fetching message list: {e}")
            return []

    async def mark_as_read(self, uid: str) -> bool:
        """
        Mark message as read
        Returns True if successful, False otherwise
        """
        if not self.connected or not self.connection:
            logger.error("Not connected to IMAP server")
            return False

        try:
            status, data = self.connection.uid('store', uid, '+FLAGS', '\\Seen')
            return status == "OK"

        except imaplib.IMAP4.error as e:
            logger.error(f"Error marking message {uid} as read: {e}")
            return False

    async def delete_message(self, uid: str) -> bool:
        """
        Delete message
        Returns True if successful, False otherwise
        """
        if not self.connected or not self.connection:
            logger.error("Not connected to IMAP server")
            return False

        try:
            # Mark for deletion
            status, data = self.connection.uid('store', uid, '+FLAGS', '\\Deleted')
            if status != "OK":
                logger.error(f"Failed to mark message {uid} for deletion: {data}")
                return False

            # Expunge to permanently delete
            status, data = self.connection.expunge()
            return status == "OK"

        except imaplib.IMAP4.error as e:
            logger.error(f"Error deleting message {uid}: {e}")
            return False

    async def _parse_email_message(self, email_message: email.message.Message, uid: str) -> Dict[str, Any]:
        """
        Parse email message and extract relevant information
        Returns dictionary with message data
        """
        try:
            # Extract headers
            subject = self._decode_header(email_message.get('Subject', ''))
            sender = self._decode_header(email_message.get('From', ''))
            date_str = email_message.get('Date', '')
            message_id = email_message.get('Message-ID', '')
            to_header = self._decode_header(email_message.get('To', ''))

            # Parse date
            received_date = self._parse_date(date_str)

            # Extract body and attachments
            body_text, body_html, attachments = self._extract_body_and_attachments(email_message)

            message_data = {
                'uid': uid,
                'subject': subject,
                'sender': sender,
                'sender_email': self._extract_email_from_header(sender),
                'to': to_header,
                'date': received_date,
                'date_str': date_str,
                'message_id': message_id,
                'body_text': body_text,
                'body_html': body_html,
                'attachments': attachments,
                'has_attachments': len(attachments) > 0,
                'attachment_count': len(attachments),
                'size': len(str(email_message))
            }

            return message_data

        except Exception as e:
            logger.error(f"Error parsing email message {uid}: {e}")
            return {
                'uid': uid,
                'subject': 'Parse Error',
                'sender': 'Unknown',
                'body_text': f'Error parsing email: {str(e)}',
                'attachments': [],
                'has_attachments': False,
                'attachment_count': 0,
                'parse_error': True
            }

    def _decode_header(self, header: str) -> str:
        """
        Decode email header properly
        Returns decoded header string
        """
        if not header:
            return ""

        try:
            decoded_parts = decode_header(header)
            decoded_header = ""

            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_header += part.decode(encoding, errors='ignore')
                    else:
                        decoded_header += part.decode('utf-8', errors='ignore')
                else:
                    decoded_header += part

            return decoded_header.strip()

        except Exception as e:
            logger.warning(f"Error decoding header '{header}': {e}")
            return header

    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse email date string to datetime object
        Returns datetime object
        """
        try:
            from email.utils import parsedate_tz, mktime_tz

            if not date_str:
                return datetime.utcnow()

            timestamp = parsedate_tz(date_str)
            if timestamp:
                return datetime.fromtimestamp(mktime_tz(timestamp))
            else:
                return datetime.utcnow()

        except Exception as e:
            logger.warning(f"Error parsing date '{date_str}': {e}")
            return datetime.utcnow()

    def _extract_email_from_header(self, header: str) -> str:
        """
        Extract email address from header string
        Returns email address
        """
        try:
            import re

            # Simple regex to extract email
            email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
            match = re.search(email_pattern, header)

            if match:
                return match.group(0).lower()
            else:
                return header

        except Exception as e:
            logger.warning(f"Error extracting email from header '{header}': {e}")
            return header

    def _extract_body_and_attachments(self, email_message: email.message.Message) -> Tuple[str, str, List[Dict]]:
        """
        Extract body text and attachments from email message
        Returns tuple: (body_text, body_html, attachments_list)
        """
        body_text = ""
        body_html = ""
        attachments = []

        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get('Content-Disposition', ''))

                    # Handle attachments
                    if 'attachment' in content_disposition:
                        attachment_data = self._extract_attachment(part)
                        if attachment_data:
                            attachments.append(attachment_data)
                        continue

                    # Handle inline content
                    elif content_type == 'text/plain' and not body_text:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            body_text = payload.decode(charset, errors='ignore')

                    elif content_type == 'text/html' and not body_html:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            body_html = payload.decode(charset, errors='ignore')

            else:
                # Single part message
                content_type = email_message.get_content_type()

                if content_type == 'text/plain':
                    payload = email_message.get_payload(decode=True)
                    if payload:
                        charset = email_message.get_content_charset() or 'utf-8'
                        body_text = payload.decode(charset, errors='ignore')

                elif content_type == 'text/html':
                    payload = email_message.get_payload(decode=True)
                    if payload:
                        charset = email_message.get_content_charset() or 'utf-8'
                        body_html = payload.decode(charset, errors='ignore')

        except Exception as e:
            logger.error(f"Error extracting body and attachments: {e}")
            body_text = f"Error extracting email content: {str(e)}"

        return body_text, body_html, attachments

    def _extract_attachment(self, part) -> Optional[Dict[str, Any]]:
        """
        Extract attachment information from email part
        Returns attachment data dictionary or None
        """
        try:
            filename = part.get_filename()
            if not filename:
                return None

            filename = self._decode_header(filename)

            # Get attachment data
            payload = part.get_payload(decode=True)
            if not payload:
                return None

            content_type = part.get_content_type()
            size = len(payload)

            attachment_data = {
                'filename': filename,
                'content_type': content_type,
                'size': size,
                'data': payload,
                'is_image': content_type.startswith('image/'),
                'is_pdf': content_type == 'application/pdf',
                'is_document': any(
                    content_type.startswith(ct) for ct in ['application/', 'text/']
                ) and not content_type.startswith('image/')
            }

            return attachment_data

        except Exception as e:
            logger.error(f"Error extracting attachment: {e}")
            return None

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test IMAP connection and return status
        Returns connection status dictionary
        """
        try:
            if not self.connected:
                connection_result = await self.connect()
                if not connection_result:
                    return {
                        "status": "failed",
                        "error": "connection_failed",
                        "message": "Failed to connect to IMAP server"
                    }

            # Try to select INBOX
            folder_result = await self.select_folder("INBOX")
            if not folder_result:
                return {
                    "status": "failed",
                    "error": "folder_selection_failed",
                    "message": "Failed to select INBOX folder"
                }

            # Get folder status
            status, data = self.connection.status('INBOX', '(MESSAGES RECENT UNSEEN)')
            folder_info = {
                "connected": True,
                "server": f"{IMAP_HOST}:{IMAP_PORT}",
                "username": IMAP_USERNAME,
                "folder": "INBOX"
            }

            if status == "OK" and data:
                # Parse folder status
                status_str = data[0].decode()
                import re
                messages = re.search(r'MESSAGES (\d+)', status_str)
                recent = re.search(r'RECENT (\d+)', status_str)
                unseen = re.search(r'UNSEEN (\d+)', status_str)

                if messages:
                    folder_info["total_messages"] = int(messages.group(1))
                if recent:
                    folder_info["recent_messages"] = int(recent.group(1))
                if unseen:
                    folder_info["unseen_messages"] = int(unseen.group(1))

            return {
                "status": "success",
                "connection_info": folder_info
            }

        except Exception as e:
            logger.error(f"IMAP connection test failed: {e}")
            return {
                "status": "failed",
                "error": "test_failed",
                "message": str(e)
            }

    async def reconnect(self) -> bool:
        """
        Reconnect to IMAP server
        Returns True if successful, False otherwise
        """
        try:
            await self.disconnect()
            await asyncio.sleep(IMAP_RETRY_DELAY)
            return await self.connect()

        except Exception as e:
            logger.error(f"Error reconnecting to IMAP: {e}")
            return False

    async def ensure_connection(self) -> bool:
        """
        Ensure connection is active, reconnect if necessary
        Returns True if connection is active, False otherwise
        """
        if not self.connected or not self.connection:
            return await self.connect()

        try:
            # Test connection with NOOP
            self.connection.noop()
            return True

        except imaplib.IMAP4.error:
            logger.info("IMAP connection lost, attempting to reconnect")
            return await self.reconnect()

        except Exception as e:
            logger.error(f"Error checking IMAP connection: {e}")
            return await self.reconnect()