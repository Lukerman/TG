"""
Inline keyboards for Telegram Temp Mail Bot
Provides interactive button layouts for user actions
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import ERROR_MESSAGES


class InlineKeyboards:
    """Factory class for creating inline keyboards"""

    @staticmethod
    def main_actions_keyboard() -> InlineKeyboardMarkup:
        """
        Create main actions keyboard
        Returns inline keyboard with primary actions
        """
        keyboard = [
            [
                InlineKeyboardButton("📥 Refresh Inbox", callback_data="refresh_inbox"),
                InlineKeyboardButton("✉️ New Email", callback_data="new_email")
            ],
            [
                InlineKeyboardButton("🗑️ Delete Temp Mail", callback_data="delete_email")
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def email_actions_keyboard(uid: str, has_attachments: bool = False) -> InlineKeyboardMarkup:
        """
        Create email actions keyboard
        Returns inline keyboard with email-specific actions
        """
        first_row = [
            InlineKeyboardButton("📧 View Full Message", callback_data=f"view_message:{uid}")
        ]

        # Add attachment button if email has attachments
        if has_attachments:
            first_row.append(InlineKeyboardButton("📎 Download All", callback_data=f"download_attachments:{uid}"))

        keyboard = [first_row]

        # Add second row with delete option
        keyboard.append([
            InlineKeyboardButton("🗑️ Delete Message", callback_data=f"delete_message:{uid}")
        ])

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
        """
        Create confirmation keyboard for actions
        Returns inline keyboard with yes/no options
        """
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes, Confirm", callback_data=f"confirm_{action}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_{action}")
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def welcome_keyboard() -> InlineKeyboardMarkup:
        """
        Create welcome keyboard for new users
        Returns inline keyboard with getting started options
        """
        keyboard = [
            [
                InlineKeyboardButton("📧 Create Temp Email", callback_data="new_email"),
                InlineKeyboardButton("📖 How it Works", callback_data="help")
            ],
            [
                InlineKeyboardButton("📥 Check Inbox", callback_data="refresh_inbox")
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def email_list_keyboard(emails: list) -> InlineKeyboardMarkup:
        """
        Create keyboard for email list
        Returns inline keyboard with email options
        """
        keyboard = []

        # Add email options (limit to 5 emails due to Telegram button limits)
        for i, email_data in enumerate(emails[:5]):
            uid = email_data.get('uid', str(i))
            sender = email_data.get('sender', 'Unknown')[:20]  # Truncate long sender names
            subject = email_data.get('subject', 'No Subject')[:25]  # Truncate long subjects

            # Create button text
            has_attachments = email_data.get('has_attachments', False)
            attachment_indicator = " 📎" if has_attachments else ""
            button_text = f"{i+1}. {sender}{attachment_indicator}"

            keyboard.append([
                InlineKeyboardButton(button_text, callback_data=f"view_message:{uid}")
            ])

        # Add action buttons at bottom
        if keyboard:
            keyboard.append([
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_inbox"),
                InlineKeyboardButton("✉️ New Email", callback_data="new_email")
            ])

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def attachment_keyboard(uid: str, attachments: list) -> InlineKeyboardMarkup:
        """
        Create keyboard for attachment actions
        Returns inline keyboard with attachment options
        """
        keyboard = []

        # Add individual attachment buttons (limit to 5 due to Telegram limits)
        for i, attachment in enumerate(attachments[:5]):
            filename = attachment.get('filename', f'attachment_{i+1}')
            # Truncate long filenames
            if len(filename) > 30:
                filename = filename[:27] + "..."

            keyboard.append([
                InlineKeyboardButton(f"📎 {filename}", callback_data=f"download_attachment:{uid}:{i}")
            ])

        # Add action buttons
        action_row = []
        action_row.append(InlineKeyboardButton("📥 Download All", callback_data=f"download_attachments:{uid}"))
        if len(attachments) > 5:
            action_row.append(InlineKeyboardButton(f"📎 {len(attachments)-5} more...", callback_data="more_attachments"))

        if action_row:
            keyboard.append(action_row)

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def help_keyboard() -> InlineKeyboardMarkup:
        """
        Create help keyboard
        Returns inline keyboard with help options
        """
        keyboard = [
            [
                InlineKeyboardButton("📧 Create Email", callback_data="new_email"),
                InlineKeyboardButton("📥 Check Inbox", callback_data="refresh_inbox")
            ],
            [
                InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
                InlineKeyboardButton("📞 Contact Support", callback_data="support")
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def settings_keyboard() -> InlineKeyboardMarkup:
        """
        Create settings keyboard
        Returns inline keyboard with setting options
        """
        keyboard = [
            [
                InlineKeyboardButton("⏰ Expiry Time", callback_data="setting_expiry"),
                InlineKeyboardButton("🔔 Notifications", callback_data="setting_notifications")
            ],
            [
                InlineKeyboardButton("📊 Statistics", callback_data="statistics"),
                InlineKeyboardButton("🗑️ Clear Data", callback_data="clear_data")
            ],
            [
                InlineKeyboardButton("❌ Close", callback_data="close_settings")
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def expiry_keyboard() -> InlineKeyboardMarkup:
        """
        Create expiry time selection keyboard
        Returns inline keyboard with expiry options
        """
        keyboard = [
            [
                InlineKeyboardButton("30 minutes", callback_data="expiry_30m"),
                InlineKeyboardButton("1 hour", callback_data="expiry_1h")
            ],
            [
                InlineKeyboardButton("2 hours", callback_data="expiry_2h"),
                InlineKeyboardButton("6 hours", callback_data="expiry_6h")
            ],
            [
                InlineKeyboardButton("12 hours", callback_data="expiry_12h"),
                InlineKeyboardButton("24 hours", callback_data="expiry_24h")
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_expiry")
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def notification_keyboard() -> InlineKeyboardMarkup:
        """
        Create notification settings keyboard
        Returns inline keyboard with notification options
        """
        keyboard = [
            [
                InlineKeyboardButton("🔔 ON", callback_data="notifications_on"),
                InlineKeyboardButton("🔕 OFF", callback_data="notifications_off")
            ],
            [
                InlineKeyboardButton("⚡ Instant", callback_data="notifications_instant"),
                InlineKeyboardButton("🕐 Batch", callback_data="notifications_batch")
            ],
            [
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_notifications")
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def empty_state_keyboard() -> InlineKeyboardMarkup:
        """
        Create keyboard for empty state (no emails)
        Returns inline keyboard with appropriate actions
        """
        keyboard = [
            [
                InlineKeyboardButton("✉️ Create New Email", callback_data="new_email"),
                InlineKeyboardButton("🔄 Check Again", callback_data="refresh_inbox")
            ],
            [
                InlineKeyboardButton("📖 Help", callback_data="help")
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def error_keyboard(error_type: str = "general") -> InlineKeyboardMarkup:
        """
        Create keyboard for error states
        Returns inline keyboard with recovery options
        """
        keyboard = []

        if error_type == "connection":
            keyboard.append([
                InlineKeyboardButton("🔄 Retry Connection", callback_data="retry_connection")
            ])

        elif error_type == "no_email":
            keyboard.append([
                InlineKeyboardButton("✉️ Create Email", callback_data="new_email")
            ])

        elif error_type == "email_expired":
            keyboard.append([
                InlineKeyboardButton("✉️ Create New Email", callback_data="new_email")
            ])

        # Add common options
        keyboard.append([
            InlineKeyboardButton("📥 Check Inbox", callback_data="refresh_inbox"),
            InlineKeyboardButton("📖 Help", callback_data="help")
        ])

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def loading_keyboard(action: str) -> InlineKeyboardMarkup:
        """
        Create keyboard with loading indicator
        Returns inline keyboard with loading state
        """
        keyboard = [
            [
                InlineKeyboardButton("⏳ Loading...", callback_data=f"loading_{action}")
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def share_email_keyboard(email: str) -> InlineKeyboardMarkup:
        """
        Create keyboard for sharing email
        Returns inline keyboard with share options
        """
        keyboard = [
            [
                InlineKeyboardButton("📋 Copy Email", callback_data=f"copy_email:{email}")
            ],
            [
                InlineKeyboardButton("📤 Share Email", callback_data=f"share_email:{email}"),
                InlineKeyboardButton("🔄 Generate New", callback_data="new_email")
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def statistics_keyboard() -> InlineKeyboardMarkup:
        """
        Create statistics keyboard
        Returns inline keyboard with statistics options
        """
        keyboard = [
            [
                InlineKeyboardButton("📊 View Stats", callback_data="view_stats"),
                InlineKeyboardButton("📈 Export Data", callback_data="export_stats")
            ],
            [
                InlineKeyboardButton("🗑️ Reset Stats", callback_data="reset_stats"),
                InlineKeyboardButton("❌ Close", callback_data="close_statistics")
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def single_button_keyboard(text: str, callback_data: str) -> InlineKeyboardMarkup:
        """
        Create keyboard with single button
        Returns inline keyboard with one button
        """
        keyboard = [
            [
                InlineKeyboardButton(text, callback_data=callback_data)
            ]
        ]

        return InlineKeyboardMarkup(keyboard)

    @staticmethod
    def create_custom_keyboard(buttons_data: list, rows: int = 2) -> InlineKeyboardMarkup:
        """
        Create custom keyboard from button data
        Args:
            buttons_data: List of tuples (text, callback_data)
            rows: Number of rows in keyboard
        Returns inline keyboard with custom buttons
        """
        keyboard = []

        for i in range(0, len(buttons_data), rows):
            row = []
            for j in range(rows):
                if i + j < len(buttons_data):
                    text, callback_data = buttons_data[i + j]
                    row.append(InlineKeyboardButton(text, callback_data=callback_data))

            if row:
                keyboard.append(row)

        return InlineKeyboardMarkup(keyboard) if keyboard else None