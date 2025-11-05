"""
Input validation utilities for Telegram Temp Mail Bot
Provides validation functions for various user inputs and data
"""

import re
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from config import (
    EMAIL_REGEX,
    USERNAME_REGEX,
    SAFE_TEXT_REGEX,
    MAX_MESSAGE_LENGTH,
    MAX_EMAIL_PREFIX_LENGTH,
    MIN_EMAIL_PREFIX_LENGTH,
    EMAIL_DOMAIN,
    EMAIL_PREFIX_LENGTH,
    EMAIL_RANDOM_LENGTH
)

logger = logging.getLogger(__name__)


class Validators:
    """Utility class for input validation"""

    @staticmethod
    def is_valid_email(email: str) -> Dict[str, Any]:
        """
        Validate email address format
        Returns validation result dictionary
        """
        try:
            if not email or not isinstance(email, str):
                return {
                    "valid": False,
                    "error": "empty_input",
                    "message": "Email cannot be empty"
                }

            email = email.strip().lower()

            # Check length
            if len(email) > 254:  # RFC 5321 limit
                return {
                    "valid": False,
                    "error": "too_long",
                    "message": "Email address is too long"
                }

            # Check basic format with regex
            if not re.match(EMAIL_REGEX, email):
                return {
                    "valid": False,
                    "error": "invalid_format",
                    "message": "Invalid email format"
                }

            # Check if it's for our domain
            if not email.endswith(f"@{EMAIL_DOMAIN}"):
                return {
                    "valid": False,
                    "error": "wrong_domain",
                    "message": f"Email must be @{EMAIL_DOMAIN}"
                }

            # Check local part format (prefix_random)
            local_part = email.split('@')[0]

            if '_' not in local_part:
                return {
                    "valid": False,
                    "error": "invalid_local_format",
                    "message": "Email must be in format: prefix_random@domain"
                }

            parts = local_part.split('_')

            if len(parts) != 2:
                return {
                    "valid": False,
                    "error": "invalid_local_format",
                    "message": "Email must have exactly one underscore separator"
                }

            prefix, random_part = parts

            # Validate prefix
            if not prefix or len(prefix) < MIN_EMAIL_PREFIX_LENGTH:
                return {
                    "valid": False,
                    "error": "invalid_prefix",
                    "message": f"Prefix must be at least {MIN_EMAIL_PREFIX_LENGTH} characters"
                }

            if len(prefix) > MAX_EMAIL_PREFIX_LENGTH:
                return {
                    "valid": False,
                    "error": "prefix_too_long",
                    "message": f"Prefix must be {MAX_EMAIL_PREFIX_LENGTH} characters or less"
                }

            if not re.match(r'^[a-z0-9]+$', prefix):
                return {
                    "valid": False,
                    "error": "invalid_prefix_chars",
                    "message": "Prefix can only contain lowercase letters and numbers"
                }

            # Validate random part
            if not random_part:
                return {
                    "valid": False,
                    "error": "missing_random",
                    "message": "Email must have a random part"
                }

            if len(random_part) != EMAIL_RANDOM_LENGTH:
                return {
                    "valid": False,
                    "error": "invalid_random_length",
                    "message": f"Random part must be {EMAIL_RANDOM_LENGTH} characters"
                }

            if not re.match(r'^[a-z0-9]+$', random_part):
                return {
                    "valid": False,
                    "error": "invalid_random_chars",
                    "message": "Random part can only contain lowercase letters and numbers"
                }

            return {
                "valid": True,
                "prefix": prefix,
                "random_part": random_part,
                "full_email": email,
                "message": "Email is valid"
            }

        except Exception as e:
            logger.error(f"Error validating email {email}: {e}")
            return {
                "valid": False,
                "error": "validation_error",
                "message": "Error validating email"
            }

    @staticmethod
    def is_valid_username(username: str) -> Dict[str, Any]:
        """
        Validate Telegram username format
        Returns validation result dictionary
        """
        try:
            if not username:
                return {
                    "valid": False,
                    "error": "empty_input",
                    "message": "Username cannot be empty"
                }

            # Remove @ if present
            clean_username = username.lstrip('@')

            # Check with regex
            if not re.match(USERNAME_REGEX, clean_username):
                return {
                    "valid": False,
                    "error": "invalid_format",
                    "message": "Username contains invalid characters"
                }

            return {
                "valid": True,
                "username": clean_username,
                "message": "Username is valid"
            }

        except Exception as e:
            logger.error(f"Error validating username {username}: {e}")
            return {
                "valid": False,
                "error": "validation_error",
                "message": "Error validating username"
            }

    @staticmethod
    def is_valid_telegram_id(telegram_id: Any) -> Dict[str, Any]:
        """
        Validate Telegram user ID
        Returns validation result dictionary
        """
        try:
            if telegram_id is None:
                return {
                    "valid": False,
                    "error": "empty_input",
                    "message": "Telegram ID cannot be empty"
                }

            # Convert to integer if possible
            try:
                user_id = int(telegram_id)
            except (ValueError, TypeError):
                return {
                    "valid": False,
                    "error": "invalid_format",
                    "message": "Telegram ID must be a number"
                }

            # Check if it's a reasonable Telegram ID (positive and within expected range)
            if user_id <= 0:
                return {
                    "valid": False,
                    "error": "invalid_range",
                    "message": "Telegram ID must be positive"
                }

            if user_id > 2**63 - 1:  # Max 64-bit signed integer
                return {
                    "valid": False,
                    "error": "too_large",
                    "message": "Telegram ID is too large"
                }

            return {
                "valid": True,
                "telegram_id": user_id,
                "message": "Telegram ID is valid"
            }

        except Exception as e:
            logger.error(f"Error validating Telegram ID {telegram_id}: {e}")
            return {
                "valid": False,
                "error": "validation_error",
                "message": "Error validating Telegram ID"
            }

    @staticmethod
    def is_valid_email_prefix(prefix: str) -> Dict[str, Any]:
        """
        Validate email prefix for custom email generation
        Returns validation result dictionary
        """
        try:
            if not prefix:
                return {
                    "valid": False,
                    "error": "empty_input",
                    "message": "Prefix cannot be empty"
                }

            # Remove spaces and convert to lowercase
            clean_prefix = re.sub(r'\s+', '', prefix.lower())

            # Check length
            if len(clean_prefix) < MIN_EMAIL_PREFIX_LENGTH:
                return {
                    "valid": False,
                    "error": "too_short",
                    "message": f"Prefix must be at least {MIN_EMAIL_PREFIX_LENGTH} characters"
                }

            if len(clean_prefix) > MAX_EMAIL_PREFIX_LENGTH:
                return {
                    "valid": False,
                    "error": "too_long",
                    "message": f"Prefix must be {MAX_EMAIL_PREFIX_LENGTH} characters or less"
                }

            # Check characters (only alphanumeric)
            if not re.match(r'^[a-z0-9]+$', clean_prefix):
                return {
                    "valid": False,
                    "error": "invalid_characters",
                    "message": "Prefix can only contain letters and numbers"
                }

            return {
                "valid": True,
                "prefix": clean_prefix,
                "message": "Prefix is valid"
            }

        except Exception as e:
            logger.error(f"Error validating email prefix {prefix}: {e}")
            return {
                "valid": False,
                "error": "validation_error",
                "message": "Error validating prefix"
            }

    @staticmethod
    def is_safe_message_text(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> Dict[str, Any]:
        """
        Validate and sanitize message text for safety
        Returns validation result dictionary
        """
        try:
            if not text:
                return {
                    "valid": False,
                    "error": "empty_input",
                    "message": "Message cannot be empty"
                }

            # Check length
            if len(text) > max_length:
                return {
                    "valid": False,
                    "error": "too_long",
                    "message": f"Message must be {max_length} characters or less"
                }

            # Check for dangerous patterns
            dangerous_patterns = [
                r'<script[^>]*>',
                r'javascript:',
                r'data:text/html',
                r'onclick=',
                r'onerror=',
                r'onload=',
                r'<iframe',
                r'<object',
                r'<embed'
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return {
                        "valid": False,
                        "error": "dangerous_content",
                        "message": "Message contains potentially dangerous content"
                    }

            # Check if it's generally safe
            if not re.match(SAFE_TEXT_REGEX, text):
                # This is a loose check, might still be safe but contains unusual characters
                return {
                    "valid": True,
                    "warning": "unusual_characters",
                    "message": "Message contains unusual characters but is probably safe"
                }

            return {
                "valid": True,
                "message": "Message is safe"
            }

        except Exception as e:
            logger.error(f"Error validating message text: {e}")
            return {
                "valid": False,
                "error": "validation_error",
                "message": "Error validating message"
            }

    @staticmethod
    def is_valid_filename(filename: str) -> Dict[str, Any]:
        """
        Validate filename for attachment handling
        Returns validation result dictionary
        """
        try:
            if not filename:
                return {
                    "valid": False,
                    "error": "empty_input",
                    "message": "Filename cannot be empty"
                }

            # Check length
            if len(filename) > 255:
                return {
                    "valid": False,
                    "error": "too_long",
                    "message": "Filename is too long"
                }

            # Check for dangerous characters
            dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0', '/', '\\']
            for char in dangerous_chars:
                if char in filename:
                    return {
                        "valid": False,
                        "error": "dangerous_characters",
                        "message": f"Filename contains dangerous character: {char}"
                    }

            # Check for reserved names (Windows)
            reserved_names = [
                'CON', 'PRN', 'AUX', 'NUL',
                'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
                'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
            ]

            name_without_ext = filename.split('.')[0].upper()
            if name_without_ext in reserved_names:
                return {
                    "valid": False,
                    "error": "reserved_name",
                    "message": "Filename is a reserved name"
                }

            # Check for hidden files (starting with .)
            if filename.startswith('.'):
                return {
                    "valid": False,
                    "error": "hidden_file",
                    "message": "Hidden files are not allowed"
                }

            # Check for suspicious extensions
            dangerous_extensions = [
                '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
                '.php', '.asp', '.aspx', '.jsp', '.sh', '.ps1', '.py', '.rb', '.pl'
            ]

            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            if '.' + file_ext in dangerous_extensions:
                return {
                    "valid": False,
                    "error": "dangerous_extension",
                    "message": f"File type .{file_ext} is not allowed"
                }

            return {
                "valid": True,
                "message": "Filename is safe"
            }

        except Exception as e:
            logger.error(f"Error validating filename {filename}: {e}")
            return {
                "valid": False,
                "error": "validation_error",
                "message": "Error validating filename"
            }

    @staticmethod
    def is_valid_mongodb_connection_string(connection_string: str) -> Dict[str, Any]:
        """
        Validate MongoDB connection string format
        Returns validation result dictionary
        """
        try:
            if not connection_string:
                return {
                    "valid": False,
                    "error": "empty_input",
                    "message": "Connection string cannot be empty"
                }

            # Basic MongoDB connection string pattern
            mongodb_pattern = r'^mongodb(\+srv)?://'

            if not re.match(mongodb_pattern, connection_string):
                return {
                    "valid": False,
                    "error": "invalid_format",
                    "message": "Invalid MongoDB connection string format"
                }

            # Check for required components
            if '@' not in connection_string:
                return {
                    "valid": False,
                    "error": "missing_credentials",
                    "message": "Connection string must contain credentials"
                }

            # Extract and validate host part
            try:
                after_at = connection_string.split('@', 1)[1]
                if not after_at or '/' not in after_at:
                    return {
                        "valid": False,
                        "error": "missing_host",
                        "message": "Connection string must contain host and database"
                    }
            except IndexError:
                return {
                    "valid": False,
                    "error": "invalid_format",
                    "message": "Invalid connection string structure"
                }

            return {
                "valid": True,
                "message": "Connection string format is valid"
            }

        except Exception as e:
            logger.error(f"Error validating MongoDB connection string: {e}")
            return {
                "valid": False,
                "error": "validation_error",
                "message": "Error validating connection string"
            }

    @staticmethod
    def is_valid_callback_data(callback_data: str) -> Dict[str, Any]:
        """
        Validate Telegram callback data format
        Returns validation result dictionary
        """
        try:
            if not callback_data:
                return {
                    "valid": False,
                    "error": "empty_input",
                    "message": "Callback data cannot be empty"
                }

            # Check length (Telegram limit is 64 bytes)
            if len(callback_data.encode('utf-8')) > 64:
                return {
                    "valid": False,
                    "error": "too_long",
                    "message": "Callback data is too long (64 byte limit)"
                }

            # Check for allowed characters (basic safety)
            allowed_pattern = r'^[a-zA-Z0-9_:.-]+$'
            if not re.match(allowed_pattern, callback_data):
                return {
                    "valid": False,
                    "error": "invalid_characters",
                    "message": "Callback data contains invalid characters"
                }

            return {
                "valid": True,
                "message": "Callback data is valid"
            }

        except Exception as e:
            logger.error(f"Error validating callback data {callback_data}: {e}")
            return {
                "valid": False,
                "error": "validation_error",
                "message": "Error validating callback data"
            }

    @staticmethod
    def is_valid_datetime_string(datetime_str: str) -> Dict[str, Any]:
        """
        Validate datetime string format
        Returns validation result dictionary
        """
        try:
            if not datetime_str:
                return {
                    "valid": False,
                    "error": "empty_input",
                    "message": "Datetime string cannot be empty"
                }

            # Try to parse with common formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%d",
            ]

            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(datetime_str, fmt)
                    return {
                        "valid": True,
                        "datetime": parsed_date,
                        "format": fmt,
                        "message": "Datetime string is valid"
                    }
                except ValueError:
                    continue

            return {
                "valid": False,
                "error": "invalid_format",
                "message": "Datetime string format is not recognized"
            }

        except Exception as e:
            logger.error(f"Error validating datetime string {datetime_str}: {e}")
            return {
                "valid": False,
                "error": "validation_error",
                "message": "Error validating datetime string"
            }

    @staticmethod
    def sanitize_text(text: str, max_length: int = None) -> str:
        """
        Sanitize text for safe display
        Returns sanitized text
        """
        try:
            if not text:
                return ""

            # Apply length limit if specified
            if max_length and len(text) > max_length:
                text = text[:max_length]

            # Remove or replace dangerous characters
            sanitized = re.sub(r'[<>"\']', '', text)

            # Remove control characters except newlines and tabs
            sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)

            # Normalize whitespace
            sanitized = re.sub(r'\s+', ' ', sanitized).strip()

            return sanitized

        except Exception as e:
            logger.error(f"Error sanitizing text: {e}")
            return text[:max_length] if max_length and len(text) > max_length else text

    @staticmethod
    def validate_email_list(emails: List[str]) -> Dict[str, Any]:
        """
        Validate a list of email addresses
        Returns validation result dictionary
        """
        try:
            if not emails:
                return {
                    "valid": False,
                    "error": "empty_input",
                    "message": "Email list cannot be empty"
                }

            if not isinstance(emails, list):
                return {
                    "valid": False,
                    "error": "invalid_format",
                    "message": "Input must be a list"
                }

            valid_emails = []
            invalid_emails = []

            for email in emails:
                result = Validators.is_valid_email(email)
                if result['valid']:
                    valid_emails.append(email)
                else:
                    invalid_emails.append({
                        'email': email,
                        'error': result['error'],
                        'message': result['message']
                    })

            return {
                "valid": len(invalid_emails) == 0,
                "valid_count": len(valid_emails),
                "invalid_count": len(invalid_emails),
                "valid_emails": valid_emails,
                "invalid_emails": invalid_emails,
                "message": f"Validated {len(emails)} emails: {len(valid_emails)} valid, {len(invalid_emails)} invalid"
            }

        except Exception as e:
            logger.error(f"Error validating email list: {e}")
            return {
                "valid": False,
                "error": "validation_error",
                "message": "Error validating email list"
            }