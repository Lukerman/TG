"""
Email address generator for Telegram Temp Mail Bot
Handles generation of unique temporary email addresses
"""

import random
import string
import logging
from typing import Optional

from config import (
    EMAIL_DOMAIN,
    EMAIL_PREFIX_LENGTH,
    EMAIL_RANDOM_LENGTH,
    EMAIL_ALLOWED_CHARS,
    EMAIL_MAX_GENERATION_ATTEMPTS
)

logger = logging.getLogger(__name__)


class EmailGenerator:
    """Generator for temporary email addresses"""

    def __init__(self, mongo_client):
        """
        Initialize email generator

        Args:
            mongo_client: MongoDB client instance for checking uniqueness
        """
        self.mongo_client = mongo_client

    def generate_random_string(self, length: int, use_lowercase_only: bool = False) -> str:
        """
        Generate a random string of specified length

        Args:
            length: Length of string to generate
            use_lowercase_only: If True, use only lowercase letters and digits

        Returns:
            Random string
        """
        if use_lowercase_only:
            chars = EMAIL_ALLOWED_CHARS
        else:
            chars = string.ascii_letters + string.digits

        return ''.join(random.choices(chars, k=length))

    def generate_user_prefix(self, custom_prefix: Optional[str] = None) -> str:
        """
        Generate or validate user prefix

        Args:
            custom_prefix: Custom prefix provided by user (optional)

        Returns:
            Validated or generated prefix
        """
        if custom_prefix:
            # Clean and validate custom prefix
            clean_prefix = ''.join(c for c in custom_prefix.lower() if c.isalnum())
            if len(clean_prefix) > EMAIL_PREFIX_LENGTH:
                clean_prefix = clean_prefix[:EMAIL_PREFIX_LENGTH]
            elif len(clean_prefix) == 0:
                clean_prefix = self.generate_random_string(EMAIL_PREFIX_LENGTH, True)
            else:
                # Pad with random characters if needed
                while len(clean_prefix) < EMAIL_PREFIX_LENGTH:
                    clean_prefix += random.choice(EMAIL_ALLOWED_CHARS)
            return clean_prefix
        else:
            # Generate random prefix
            return self.generate_random_string(EMAIL_PREFIX_LENGTH, True)

    async def generate_unique_email(self, telegram_id: int, custom_prefix: Optional[str] = None) -> str:
        """
        Generate a unique temporary email address

        Args:
            telegram_id: User's Telegram ID
            custom_prefix: Optional custom prefix for the email

        Returns:
            Unique temporary email address

        Raises:
            ValueError: If unable to generate unique email after max attempts
        """
        prefix = self.generate_user_prefix(custom_prefix)

        for attempt in range(EMAIL_MAX_GENERATION_ATTEMPTS):
            try:
                # Generate random suffix
                random_suffix = self.generate_random_string(EMAIL_RANDOM_LENGTH, True)

                # Combine parts to create email
                email = f"{prefix}_{random_suffix}@{EMAIL_DOMAIN}"

                # Check if email is unique
                existing_user = await self.mongo_client.get_user_by_email(email, active_only=False)

                if existing_user is None:
                    logger.info(f"Generated unique email: {email} for user {telegram_id}")
                    return email

                logger.debug(f"Email {email} already exists, trying again (attempt {attempt + 1})")

            except Exception as e:
                logger.error(f"Error checking email uniqueness: {e}")
                # Continue trying even if there's an error

        # If we reach here, we couldn't generate a unique email
        error_msg = f"Failed to generate unique email after {EMAIL_MAX_GENERATION_ATTEMPTS} attempts"
        logger.error(error_msg)
        raise ValueError(error_msg)

    async def generate_email_with_validation(self, telegram_id: int, custom_prefix: Optional[str] = None) -> dict:
        """
        Generate email with full validation and return detailed information

        Args:
            telegram_id: User's Telegram ID
            custom_prefix: Optional custom prefix

        Returns:
            Dictionary with email generation details
        """
        try:
            # Check if user already has an active email
            existing_user = await self.mongo_client.get_user(telegram_id)

            if existing_user:
                return {
                    "success": False,
                    "error": "user_already_has_email",
                    "existing_email": existing_user.get("email"),
                    "message": "You already have an active temporary email"
                }

            # Generate unique email
            email = await self.generate_unique_email(telegram_id, custom_prefix)

            # Extract prefix for storage
            prefix = email.split('@')[0].split('_')[0]

            return {
                "success": True,
                "email": email,
                "prefix": prefix,
                "domain": EMAIL_DOMAIN,
                "custom_prefix_used": custom_prefix is not None,
                "message": "Email generated successfully"
            }

        except ValueError as e:
            return {
                "success": False,
                "error": "generation_failed",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error in generate_email_with_validation: {e}")
            return {
                "success": False,
                "error": "unexpected_error",
                "message": "An unexpected error occurred while generating email"
            }

    def validate_custom_prefix(self, prefix: str) -> dict:
        """
        Validate a custom prefix provided by user

        Args:
            prefix: Custom prefix to validate

        Returns:
            Dictionary with validation result
        """
        if not prefix:
            return {
                "valid": False,
                "error": "empty_prefix",
                "message": "Prefix cannot be empty"
            }

        # Remove non-alphanumeric characters
        clean_prefix = ''.join(c for c in prefix.lower() if c.isalnum())

        if not clean_prefix:
            return {
                "valid": False,
                "error": "invalid_characters",
                "message": "Prefix must contain only letters and numbers"
            }

        if len(clean_prefix) > EMAIL_PREFIX_LENGTH:
            return {
                "valid": False,
                "error": "too_long",
                "message": f"Prefix must be {EMAIL_PREFIX_LENGTH} characters or less"
            }

        if len(clean_prefix) < 3:
            return {
                "valid": False,
                "error": "too_short",
                "message": "Prefix must be at least 3 characters long"
            }

        return {
            "valid": True,
            "clean_prefix": clean_prefix,
            "message": "Prefix is valid"
        }

    def get_email_info(self, email: str) -> dict:
        """
        Extract information from an email address

        Args:
            email: Email address to analyze

        Returns:
            Dictionary with email information
        """
        try:
            if '@' not in email:
                return {
                    "valid": False,
                    "error": "invalid_format",
                    "message": "Invalid email format"
                }

            local_part, domain = email.split('@', 1)

            if domain != EMAIL_DOMAIN:
                return {
                    "valid": False,
                    "error": "wrong_domain",
                    "message": f"Email must be @{EMAIL_DOMAIN}"
                }

            if '_' not in local_part:
                return {
                    "valid": False,
                    "error": "invalid_format",
                    "message": "Email must be in format: prefix_random@domain"
                }

            prefix, random_part = local_part.split('_', 1)

            return {
                "valid": True,
                "prefix": prefix,
                "random_part": random_part,
                "domain": domain,
                "full_email": email
            }

        except Exception as e:
            logger.error(f"Error parsing email {email}: {e}")
            return {
                "valid": False,
                "error": "parsing_error",
                "message": "Error parsing email address"
            }

    async def suggest_email_variations(self, base_prefix: str, telegram_id: int) -> list:
        """
        Suggest email variations based on a base prefix

        Args:
            base_prefix: Base prefix to use
            telegram_id: User's Telegram ID for uniqueness checks

        Returns:
            List of suggested email variations
        """
        suggestions = []

        # Validate base prefix
        validation_result = self.validate_custom_prefix(base_prefix)
        if not validation_result["valid"]:
            base_prefix = self.generate_user_prefix()
        else:
            base_prefix = validation_result["clean_prefix"]

        # Generate multiple variations
        for i in range(5):  # Generate 5 suggestions
            try:
                # Try different random suffix lengths for variety
                suffix_length = EMAIL_RANDOM_LENGTH + (i % 3) - 1  # Vary between -1, 0, +1
                suffix_length = max(6, min(10, suffix_length))  # Keep between 6 and 10

                random_suffix = self.generate_random_string(suffix_length, True)
                suggested_email = f"{base_prefix}_{random_suffix}@{EMAIL_DOMAIN}"

                # Check if it's actually unique
                existing_user = await self.mongo_client.get_user_by_email(suggested_email, active_only=False)

                if existing_user is None:
                    suggestions.append(suggested_email)

            except Exception as e:
                logger.debug(f"Error generating suggestion {i}: {e}")
                continue

        # If we couldn't generate any unique suggestions, generate some random ones
        if not suggestions:
            for i in range(3):
                try:
                    random_email = await self.generate_unique_email(telegram_id)
                    suggestions.append(random_email)
                except:
                    continue

        return suggestions[:5]  # Return max 5 suggestions