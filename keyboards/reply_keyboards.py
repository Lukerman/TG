"""
Reply keyboards for Telegram Temp Mail Bot
Provides persistent keyboard layouts for user interactions
"""

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton

from config import BOT_ALLOW_SENDING_WITHOUT_REPLY


class ReplyKeyboards:
    """Factory class for creating reply keyboards"""

    @staticmethod
    def main_reply_keyboard(resize_keyboard: bool = True) -> ReplyKeyboardMarkup:
        """
        Create main reply keyboard with primary actions
        Returns ReplyKeyboardMarkup with main options
        """
        keyboard = [
            ["📥 Inbox"],
            ["✉️ New Email"],
            ["🔁 Refresh"],
            ["🗑️ Delete"]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=False,
            input_field_placeholder="Choose an action..."
        )

    @staticmethod
    def compact_main_keyboard(resize_keyboard: bool = True) -> ReplyKeyboardMarkup:
        """
        Create compact main keyboard (2x2 layout)
        Returns ReplyKeyboardMarkup with compact layout
        """
        keyboard = [
            ["📥 Inbox", "✉️ New Email"],
            ["🔁 Refresh", "🗑️ Delete"]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=False,
            input_field_placeholder="Select option..."
        )

    @staticmethod
    def welcome_keyboard(resize_keyboard: bool = True) -> ReplyKeyboardMarkup:
        """
        Create welcome keyboard for new users
        Returns ReplyKeyboardMarkup with welcome options
        """
        keyboard = [
            ["📧 Create Temp Email", "📥 Check Inbox"],
            ["📖 Help", "⚙️ Settings"]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=False,
            input_field_placeholder="Get started..."
        )

    @staticmethod
    def email_actions_keyboard(resize_keyboard: bool = True) -> ReplyKeyboardMarkup:
        """
        Create keyboard for email-specific actions
        Returns ReplyKeyboardMarkup with email options
        """
        keyboard = [
            ["📧 View Full Message"],
            ["📎 Download Attachments"],
            ["🗑️ Delete Message"],
            ["🔙 Back to Inbox"]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Choose action..."
        )

    @staticmethod
    def email_management_keyboard(resize_keyboard: bool = True) -> ReplyKeyboardMarkup:
        """
        Create keyboard for email management
        Returns ReplyKeyboardMarkup with management options
        """
        keyboard = [
            ["📥 Inbox", "✉️ New Email"],
            ["🔁 Refresh", "📊 Statistics"],
            ["🗑️ Delete", "⚙️ Settings"]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=False,
            input_field_placeholder="Manage emails..."
        )

    @staticmethod
    def settings_keyboard(resize_keyboard: bool = True) -> ReplyKeyboardMarkup:
        """
        Create keyboard for settings
        Returns ReplyKeyboardMarkup with setting options
        """
        keyboard = [
            ["⏰ Expiry Time", "🔔 Notifications"],
            ["📊 Statistics", "🗑️ Clear Data"],
            ["🔙 Back"]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Settings..."
        )

    @staticmethod
    def confirmation_keyboard(resize_keyboard: bool = True) -> ReplyKeyboardMarkup:
        """
        Create keyboard for confirmations
        Returns ReplyKeyboardMarkup with yes/no options
        """
        keyboard = [
            ["✅ Yes", "❌ No"]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Confirm action..."
        )

    @staticmethod
    def help_keyboard(resize_keyboard: bool = True) -> ReplyKeyboardMarkup:
        """
        Create keyboard for help section
        Returns ReplyKeyboardMarkup with help options
        """
        keyboard = [
            ["📧 Create Email", "📥 Check Inbox"],
            ["⚙️ Settings", "📊 Statistics"],
            ["📞 Contact Support", "🔙 Main Menu"]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Need help?"
        )

    @staticmethod
    def admin_keyboard(resize_keyboard: bool = True) -> ReplyKeyboardMarkup:
        """
        Create admin keyboard for administrative functions
        Returns ReplyKeyboardMarkup with admin options
        """
        keyboard = [
            ["📊 System Stats", "👥 User Management"],
            ["🔧 Maintenance", "📝 Logs"],
            ["🔙 Exit Admin"]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Admin panel..."
        )

    @staticmethod
    def empty_state_keyboard(resize_keyboard: bool = True) -> ReplyKeyboardMarkup:
        """
        Create keyboard for empty states
        Returns ReplyKeyboardMarkup with recovery options
        """
        keyboard = [
            ["✉️ Create Email"],
            ["🔄 Refresh"],
            ["📖 Help"]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="No emails found"
        )

    @staticmethod
    def error_recovery_keyboard(resize_keyboard: bool = True) -> ReplyKeyboardMarkup:
        """
        Create keyboard for error recovery
        Returns ReplyKeyboardMarkup with recovery options
        """
        keyboard = [
            ["🔄 Retry", "📥 Inbox"],
            ["✉️ New Email", "📖 Help"]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Something went wrong..."
        )

    @staticmethod
    def navigation_keyboard(resize_keyboard: bool = True) -> ReplyKeyboardMarkup:
        """
        Create navigation keyboard
        Returns ReplyKeyboardMarkup with navigation options
        """
        keyboard = [
            ["🔙 Back", "🏠 Home"],
            ["⬆️ Up", "🔄 Refresh"]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Navigate..."
        )

    @staticmethod
    def quick_actions_keyboard(resize_keyboard: bool = True) -> ReplyKeyboardMarkup:
        """
        Create quick actions keyboard
        Returns ReplyKeyboardMarkup with quick actions
        """
        keyboard = [
            ["📥 Inbox", "✉️ New"],
            ["🔄 Refresh", "🗑️ Delete"]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=False,
            input_field_placeholder="Quick action..."
        )

    @staticmethod
    def experimental_features_keyboard(resize_keyboard: bool = True) -> ReplyKeyboardMarkup:
        """
        Create keyboard for experimental features
        Returns ReplyKeyboardMarkup with experimental options
        """
        keyboard = [
            ["🔄 Auto-refresh", "📧 Email Forwarding"],
            ["📊 Advanced Stats", "🔍 Search"],
            ["🔙 Back"]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Experimental features..."
        )

    @staticmethod
    def feedback_keyboard(resize_keyboard: bool = True) -> ReplyKeyboardMarkup:
        """
        Create keyboard for feedback and support
        Returns ReplyKeyboardMarkup with feedback options
        """
        keyboard = [
            ["⭐ Rate Bot", "📝 Send Feedback"],
            ["🐛 Report Bug", "💡 Suggest Feature"],
            ["🔙 Back"]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Feedback & Support"
        )

    @staticmethod
    def remove_keyboard() -> ReplyKeyboardRemove:
        """
        Remove reply keyboard
        Returns ReplyKeyboardRemove to hide keyboard
        """
        return ReplyKeyboardRemove()

    @staticmethod
    def create_location_keyboard(resize_keyboard: bool = True) -> ReplyKeyboardMarkup:
        """
        Create keyboard with location request button
        Returns ReplyKeyboardMarkup with location option
        """
        keyboard = [
            [KeyboardButton("📍 Send Location", request_location=True)],
            ["🔙 Cancel"]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Share location..."
        )

    @staticmethod
    def create_contact_keyboard(resize_keyboard: bool = True) -> ReplyKeyboardMarkup:
        """
        Create keyboard with contact request button
        Returns ReplyKeyboardMarkup with contact option
        """
        keyboard = [
            [KeyboardButton("📞 Send Contact", request_contact=True)],
            ["🔙 Cancel"]
        ]

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Share contact..."
        )

    @staticmethod
    def create_custom_keyboard(buttons: list, rows: int = 2,
                             resize_keyboard: bool = True,
                             one_time_keyboard: bool = False,
                             input_field_placeholder: str = None) -> ReplyKeyboardMarkup:
        """
        Create custom keyboard from button list
        Args:
            buttons: List of button texts
            rows: Number of rows in keyboard
            resize_keyboard: Whether to resize keyboard
            one_time_keyboard: Whether keyboard is one-time
            input_field_placeholder: Placeholder text for input field
        Returns ReplyKeyboardMarkup with custom buttons
        """
        keyboard = []

        for i in range(0, len(buttons), rows):
            row = []
            for j in range(rows):
                if i + j < len(buttons):
                    row.append(buttons[i + j])

            if row:
                keyboard.append(row)

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=one_time_keyboard,
            input_field_placeholder=input_field_placeholder
        )

    @staticmethod
    def create_menu_keyboard(options: dict, resize_keyboard: bool = True) -> ReplyKeyboardMarkup:
        """
        Create keyboard from menu options dictionary
        Args:
            options: Dictionary where keys are button texts, values are callback data
            resize_keyboard: Whether to resize keyboard
        Returns ReplyKeyboardMarkup with menu options
        """
        keyboard = []

        for text, _ in options.items():
            keyboard.append([text])

        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=resize_keyboard,
            one_time_keyboard=True,
            input_field_placeholder="Choose option..."
        )