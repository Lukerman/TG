#!/usr/bin/env python3
"""
Telegram Temp Mail Bot
A fully functional Telegram bot that provides temporary email addresses with IMAP inbox functionality.

Features:
- Generate temporary email addresses @seveton.site
- Full IMAP inbox functionality with attachment support
- MongoDB integration for user data storage
- Inline and reply keyboards
- Auto-expiring email addresses
- Background email fetching
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Add project root to path for imports
sys.path.append(str(Path(__file__).parent))

from config import TELEGRAM_BOT_TOKEN, BACKGROUND_FETCH_INTERVAL, CLEANUP_INTERVAL
from database.mongo_client import MongoDBClient
from handlers.command_handlers import CommandHandlers
from handlers.callback_handlers import CallbackHandlers
from handlers.message_handlers import MessageHandlers
from utils.background_tasks import BackgroundTasks
from keyboards.reply_keyboards import main_reply_keyboard

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TempMailBot:
    """Main Telegram Temp Mail Bot class"""

    def __init__(self):
        """Initialize the bot with all necessary components"""
        self.application = None
        self.mongo_client = None
        self.background_tasks = None
        self.running = False

    async def initialize(self):
        """Initialize all bot components"""
        try:
            logger.info("Initializing Telegram Temp Mail Bot...")

            # Initialize MongoDB client
            self.mongo_client = MongoDBClient()
            await self.mongo_client.connect()
            logger.info("MongoDB client initialized")

            # Initialize background tasks
            self.background_tasks = BackgroundTasks(self.mongo_client)

            # Create Telegram application
            self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

            # Initialize handlers
            command_handlers = CommandHandlers(self.mongo_client)
            callback_handlers = CallbackHandlers(self.mongo_client)
            message_handlers = MessageHandlers(self.mongo_client)

            # Register command handlers
            self.application.add_handler(CommandHandler("start", command_handlers.start_command))
            self.application.add_handler(CommandHandler("new", command_handlers.new_email_command))
            self.application.add_handler(CommandHandler("inbox", command_handlers.inbox_command))
            self.application.add_handler(CommandHandler("refresh", command_handlers.refresh_command))
            self.application.add_handler(CommandHandler("delete", command_handlers.delete_command))
            self.application.add_handler(CommandHandler("help", command_handlers.help_command))

            # Register callback handlers
            self.application.add_handler(CallbackQueryHandler(callback_handlers.callback_handler))

            # Register message handlers
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, message_handlers.text_message_handler)
            )

            logger.info("All handlers registered successfully")

        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            raise

    async def start_background_tasks(self):
        """Start background tasks for email fetching and cleanup"""
        try:
            # Start email fetching task
            asyncio.create_task(self.background_tasks.email_fetching_loop())
            logger.info("Email fetching task started")

            # Start cleanup task
            asyncio.create_task(self.background_tasks.cleanup_loop())
            logger.info("Cleanup task started")

        except Exception as e:
            logger.error(f"Failed to start background tasks: {e}")
            raise

    async def run(self):
        """Run the bot"""
        try:
            await self.initialize()
            await self.start_background_tasks()

            logger.info("Starting Telegram Temp Mail Bot...")
            self.running = True

            # Start polling
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(drop_pending_updates=True)

            logger.info("Bot is now running. Press Ctrl+C to stop.")

            # Keep the bot running
            while self.running:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Gracefully shutdown the bot"""
        logger.info("Shutting down bot...")
        self.running = False

        try:
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("Telegram application stopped")

            if self.background_tasks:
                self.background_tasks.stop()
                logger.info("Background tasks stopped")

            if self.mongo_client:
                await self.mongo_client.close()
                logger.info("MongoDB connection closed")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

        logger.info("Bot shutdown complete")


async def main():
    """Main function to run the bot"""
    bot = TempMailBot()

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(bot.shutdown())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the bot
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)