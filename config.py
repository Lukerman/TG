"""
Configuration file for Telegram Temp Mail Bot
Contains all settings, credentials, and constants
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# ============================================
# TELEGRAM BOT CONFIGURATION
# ============================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")

# ============================================
# MONGODB CONFIGURATION
# ============================================
MONGO_CONNECTION_STRING = os.getenv(
    "MONGO_CONNECTION_STRING",
    "mongodb+srv://infinityfilehelper_db_user:SKFcZ1axjhtw4Ff5@cluster0.46srj4w.mongodb.net/?appName=Cluster0"
)
MONGO_DATABASE_NAME = os.getenv("MONGO_DATABASE_NAME", "temp_mail_bot")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "users")

# MongoDB connection settings
MONGO_MAX_POOL_SIZE = 10
MONGO_SERVER_SELECTION_TIMEOUT = 5000  # milliseconds
MONGO_CONNECT_TIMEOUT = 5000  # milliseconds

# ============================================
# IMAP SERVER CONFIGURATION
# ============================================
IMAP_HOST = os.getenv("IMAP_HOST", "mail.seveton.site")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_USERNAME = os.getenv("IMAP_USERNAME", "admin@seveton.site")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "Aezakmi@ff135")
IMAP_USE_SSL = os.getenv("IMAP_USE_SSL", "True").lower() == "true"

# IMAP connection settings
IMAP_CONNECTION_TIMEOUT = 30  # seconds
IMAP_READ_TIMEOUT = 60  # seconds
IMAP_MAX_RETRIES = 3
IMAP_RETRY_DELAY = 2  # seconds

# ============================================
# EMAIL CONFIGURATION
# ============================================
EMAIL_DOMAIN = os.getenv("EMAIL_DOMAIN", "seveton.site")
EMAIL_EXPIRY_TIME = timedelta(hours=1)  # 1 hour
EMAIL_PREFIX_LENGTH = 6  # User-defined prefix length
EMAIL_RANDOM_LENGTH = 8   # Random characters length

# Email generation settings
EMAIL_MAX_GENERATION_ATTEMPTS = 10
EMAIL_ALLOWED_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789"  # For random part

# ============================================
# BOT CONFIGURATION
# ============================================
MAX_INBOX_MESSAGES = int(os.getenv("MAX_INBOX_MESSAGES", "5"))
REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "30"))  # seconds
BACKGROUND_FETCH_INTERVAL = int(os.getenv("BACKGROUND_FETCH_INTERVAL", "60"))  # seconds
CLEANUP_INTERVAL = int(os.getenv("CLEANUP_INTERVAL", "300"))  # seconds (5 minutes)

# Bot behavior settings
BOT_PARSE_MODE = "HTML"
BOT_DISABLE_WEB_PAGE_PREVIEW = True
BOT_ALLOW_SENDING_WITHOUT_REPLY = True

# ============================================
# FILE HANDLING CONFIGURATION
# ============================================
MAX_ATTACHMENT_SIZE = None  # Let Telegram handle limits (default 50MB)
SUPPORTED_ATTACHMENT_TYPES = None  # Auto-detect all types

# File download settings
TEMP_FILE_DIR = "temp_downloads"
MAX_TEMP_FILE_AGE = 3600  # seconds (1 hour)

# Supported attachment extensions (auto-detect, but these get special handling)
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'}
DOCUMENT_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx'}
ARCHIVE_EXTENSIONS = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'}

# ============================================
# LOGGING CONFIGURATION
# ============================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "bot.log")
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# ============================================
# RATE LIMITING CONFIGURATION
# ============================================
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
RATE_LIMIT_MESSAGES_PER_MINUTE = int(os.getenv("RATE_LIMIT_MESSAGES_PER_MINUTE", "30"))
RATE_LIMIT_EMAILS_PER_HOUR = int(os.getenv("RATE_LIMIT_EMAILS_PER_HOUR", "10"))

# ============================================
# ERROR HANDLING CONFIGURATION
# ============================================
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAY_BASE = 1  # seconds (exponential backoff)
ERROR_NOTIFICATION_ENABLED = True

# ============================================
# SECURITY CONFIGURATION
# ============================================
# Input validation
MAX_MESSAGE_LENGTH = 4096
MAX_EMAIL_PREFIX_LENGTH = 20
MIN_EMAIL_PREFIX_LENGTH = 3

# Content sanitization
SANITIZE_EMAIL_CONTENT = True
ALLOWED_HTML_TAGS = {'b', 'i', 'u', 'strong', 'em', 'a', 'br', 'p'}
BLOCKED_PATTERNS = [
    'javascript:',
    'data:text/html',
    '<script',
    'onclick=',
    'onerror='
]

# ============================================
# DEVELOPMENT/DEBUG CONFIGURATION
# ============================================
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "False").lower() == "true"

# Debug settings
DEBUG_IMAP_CONNECTIONS = DEBUG_MODE
DEBUG_MONGODB_QUERIES = DEBUG_MODE
DEBUG_EMAIL_PROCESSING = DEBUG_MODE
SAVE_FAILED_EMAILS = DEBUG_MODE

# ============================================
# MONITORING CONFIGURATION
# ============================================
MONITORING_ENABLED = os.getenv("MONITORING_ENABLED", "False").lower() == "true"
STATISTICS_COLLECTION = True

# Performance monitoring
TRACK_RESPONSE_TIMES = True
TRACK_ERROR_RATES = True
TRACK_USER_ACTIVITY = True

# ============================================
# NOTIFICATION CONFIGURATION
# ============================================
# New email notifications
NEW_EMAIL_NOTIFICATIONS_ENABLED = True
NEW_EMAIL_NOTIFICATION_DELAY = 5  # seconds

# Error notifications
ERROR_NOTIFICATION_CHAT_ID = os.getenv("ERROR_NOTIFICATION_CHAT_ID")
SEND_ERROR_NOTIFICATIONS = bool(ERROR_NOTIFICATION_CHAT_ID)

# ============================================
# BACKUP CONFIGURATION
# ============================================
BACKUP_ENABLED = os.getenv("BACKUP_ENABLED", "False").lower() == "true"
BACKUP_INTERVAL = timedelta(hours=24)  # Daily backups
BACKUP_RETENTION_PERIOD = timedelta(days=7)  # Keep backups for 7 days

# ============================================
# FEATURE FLAGS
# ============================================
ENABLE_EMAIL_FORWARDING = False
ENABLE_EMAIL_SENDING = False
ENABLE_USER_STATISTICS = True
ENABLE_EMAIL_SEARCH = True
ENABLE_EXPORT_FUNCTIONALITY = False

# ============================================
# MESSAGES AND TEMPLATES
# ============================================

# Welcome message
WELCOME_MESSAGE = """
🎉 <b>Welcome to Temp Mail Bot!</b>

📧 I'll create a temporary email address for you at <code>@seveton.site</code>

✨ <b>Features:</b>
• Receive emails with attachments
• Auto-expiring addresses
• Secure IMAP connection
• Real-time inbox updates

Use the buttons below or type /help to see all commands.
"""

# Help message
HELP_MESSAGE = """
📖 <b>Temp Mail Bot Help</b>

<b>Commands:</b>
/start - Start bot and create email
/new - Generate new temp email
/inbox - Show your inbox
/refresh - Check for new emails
/delete - Delete your temp email
/help - Show this help message

<b>Features:</b>
• 📧 Receive emails instantly
• 📎 Download attachments
• 🔒 Secure IMAP connection
• ⏰ Auto-expiring emails (1 hour)
• 🔄 Real-time updates

<b>Inline Buttons:</b>
• 📥 Refresh Inbox
• ✉️ New Email
• 🗑️ Delete Temp Mail

<b>Reply Keyboard:</b>
• 📥 Inbox
• ✉️ New Email
• 🔁 Refresh
• 🗑️ Delete

Need help? Contact support!
"""

# Error messages
ERROR_MESSAGES = {
    'general': "❌ An error occurred. Please try again later.",
    'connection': "🔌 Connection error. Please try again in a moment.",
    'no_email': "📭 You don't have a temporary email yet. Use /new to create one.",
    'email_expired': "⏰ Your temporary email has expired. Use /new to create a new one.",
    'generation_failed': "❌ Failed to generate email. Please try again.",
    'imap_error': "📧 Email service temporarily unavailable. Please try again later.",
    'mongo_error': "🗄️ Database error. Please try again later.",
    'rate_limit': "⏱️ Too many requests. Please wait a moment before trying again.",
    'invalid_input': "❌ Invalid input. Please check and try again.",
    'attachment_error': "📎 Failed to process attachment.",
    'delete_confirm': "Are you sure you want to delete your temporary email?",
}

# Success messages
SUCCESS_MESSAGES = {
    'email_created': "✅ Your temporary email is ready!",
    'email_deleted': "🗑️ Your temporary email has been deleted.",
    'inbox_refreshed': "🔄 Inbox refreshed successfully!",
    'no_new_emails': "📭 No new emails in your inbox.",
    'cleanup_completed': "🧹 Cleanup completed successfully.",
}

# Loading messages
LOADING_MESSAGES = [
    "⏳ Checking your inbox...",
    "🔄 Refreshing emails...",
    "📧 Processing new messages...",
    "⚡ Almost there...",
]

# ============================================
# VALIDATION PATTERNS
# ============================================

# Email validation regex
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

# User input validation
USERNAME_REGEX = r'^[a-zA-Z0-9_]{3,32}$'
SAFE_TEXT_REGEX = r'^[a-zA-Z0-9\s\-_.,!?@#$%&*()]+$'

# ============================================
# ENVIRONMENT VARIABLES VALIDATION
# ============================================

def validate_config():
    """Validate critical configuration settings"""
    errors = []

    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN":
        errors.append("TELEGRAM_BOT_TOKEN is not set")

    if not MONGO_CONNECTION_STRING:
        errors.append("MONGO_CONNECTION_STRING is not set")

    if not IMAP_HOST or not IMAP_USERNAME or not IMAP_PASSWORD:
        errors.append("IMAP credentials are not properly configured")

    if errors:
        raise ValueError("Configuration validation failed:\n" + "\n".join(errors))

    return True

# Validate configuration on import
if not DEVELOPMENT_MODE:
    try:
        validate_config()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("Please set the required environment variables and restart the bot.")
        exit(1)