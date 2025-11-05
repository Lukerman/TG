"""
Background tasks for Telegram Temp Mail Bot
Handles periodic email fetching, cleanup, and maintenance tasks
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from config import (
    BACKGROUND_FETCH_INTERVAL,
    CLEANUP_INTERVAL,
    NEW_EMAIL_NOTIFICATIONS_ENABLED,
    NEW_EMAIL_NOTIFICATION_DELAY,
    MAX_INBOX_MESSAGES,
    MONITORING_ENABLED
)
from email.imap_client import IMAPClient
from email.email_parser import EmailParser

logger = logging.getLogger(__name__)


class BackgroundTasks:
    """Manager for background tasks"""

    def __init__(self, mongo_client):
        """
        Initialize background tasks manager

        Args:
            mongo_client: MongoDB client instance
        """
        self.mongo_client = mongo_client
        self.imap_client = IMAPClient()
        self.email_parser = EmailParser()
        self.running = False
        self.tasks = []
        self.stats = {
            'emails_processed': 0,
            'attachments_processed': 0,
            'errors_encountered': 0,
            'last_fetch_time': None,
            'last_cleanup_time': None,
            'tasks_running': 0
        }

    def stop(self):
        """Stop all background tasks"""
        self.running = False
        logger.info("Background tasks stop requested")

    async def email_fetching_loop(self):
        """
        Background loop for fetching emails for all active users
        Runs indefinitely until stopped
        """
        logger.info("Starting email fetching loop")

        while self.running:
            try:
                self.stats['tasks_running'] += 1
                await self._fetch_emails_for_all_users()
                await asyncio.sleep(BACKGROUND_FETCH_INTERVAL)
            except asyncio.CancelledError:
                logger.info("Email fetching loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in email fetching loop: {e}")
                self.stats['errors_encountered'] += 1
                await asyncio.sleep(min(BACKGROUND_FETCH_INTERVAL, 60))  # Wait at least 1 minute on error
            finally:
                self.stats['tasks_running'] -= 1

        logger.info("Email fetching loop stopped")

    async def cleanup_loop(self):
        """
        Background loop for cleaning up expired data
        Runs indefinitely until stopped
        """
        logger.info("Starting cleanup loop")

        while self.running:
            try:
                self.stats['tasks_running'] += 1
                await self._perform_cleanup_tasks()
                await asyncio.sleep(CLEANUP_INTERVAL)
            except asyncio.CancelledError:
                logger.info("Cleanup loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                self.stats['errors_encountered'] += 1
                await asyncio.sleep(min(CLEANUP_INTERVAL, 300))  # Wait at least 5 minutes on error
            finally:
                self.stats['tasks_running'] -= 1

        logger.info("Cleanup loop stopped")

    async def _fetch_emails_for_all_users(self):
        """
        Fetch emails for all active users
        """
        try:
            # Get all active users
            active_users = await self.mongo_client.get_all_active_users()

            if not active_users:
                logger.debug("No active users to check")
                return

            logger.info(f"Checking emails for {len(active_users)} active users")

            # Ensure IMAP connection is active
            if not await self.imap_client.ensure_connection():
                logger.error("Failed to establish IMAP connection")
                return

            # Process each user
            for user_data in active_users:
                try:
                    await self._fetch_emails_for_user(user_data)
                except Exception as e:
                    logger.error(f"Error fetching emails for user {user_data.get('telegram_id')}: {e}")
                    self.stats['errors_encountered'] += 1
                    continue

            self.stats['last_fetch_time'] = datetime.utcnow()

            if MONITORING_ENABLED:
                await self._log_fetch_statistics(len(active_users))

        except Exception as e:
            logger.error(f"Error in _fetch_emails_for_all_users: {e}")
            self.stats['errors_encountered'] += 1

    async def _fetch_emails_for_user(self, user_data: Dict[str, Any]):
        """
        Fetch emails for a specific user
        """
        try:
            telegram_id = user_data.get('telegram_id')
            email = user_data.get('email')
            last_checked = user_data.get('last_checked', datetime.utcnow() - timedelta(hours=1))

            if not email:
                logger.warning(f"User {telegram_id} has no email address")
                return

            # Search for new emails since last check
            messages = await self.imap_client.fetch_message_list(
                email,
                limit=MAX_INBOX_MESSAGES,
                since_date=last_checked
            )

            if not messages:
                logger.debug(f"No new emails for user {telegram_id}")
                return

            logger.info(f"Found {len(messages)} new emails for user {telegram_id}")

            # Process new messages
            new_message_count = 0
            for message_data in messages:
                try:
                    await self._process_new_message(telegram_id, message_data)
                    new_message_count += 1
                except Exception as e:
                    logger.error(f"Error processing message for user {telegram_id}: {e}")
                    self.stats['errors_encountered'] += 1
                    continue

            # Update user's message count and last checked time
            if new_message_count > 0:
                await self.mongo_client.increment_message_count(telegram_id)
                await self.mongo_client.update_last_checked(telegram_id)

                # Send notification if enabled
                if NEW_EMAIL_NOTIFICATIONS_ENABLED:
                    await self._send_new_email_notification(telegram_id, new_message_count)

                self.stats['emails_processed'] += new_message_count

        except Exception as e:
            logger.error(f"Error in _fetch_emails_for_user: {e}")
            self.stats['errors_encountered'] += 1

    async def _process_new_message(self, telegram_id: int, message_data: Dict[str, Any]):
        """
        Process a new email message
        """
        try:
            # Log the new message
            sender = message_data.get('sender', 'Unknown')
            subject = message_data.get('subject', 'No Subject')
            has_attachments = message_data.get('has_attachments', False)
            attachment_count = message_data.get('attachment_count', 0)

            logger.debug(f"Processing message from {sender} for user {telegram_id}")

            # Process attachments if any
            if has_attachments:
                attachments = message_data.get('attachments', [])
                for attachment in attachments:
                    try:
                        # Prepare attachment for potential future use
                        prepared = await self.email_parser.prepare_attachment_for_telegram(attachment)
                        if prepared:
                            self.stats['attachments_processed'] += 1
                    except Exception as e:
                        logger.error(f"Error preparing attachment: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error in _process_new_message: {e}")
            self.stats['errors_encountered'] += 1

    async def _send_new_email_notification(self, telegram_id: int, message_count: int):
        """
        Send notification about new emails to user
        """
        try:
            # Note: This would require access to the Telegram bot instance
            # For now, we'll just log the notification
            logger.info(f"Would send notification to user {telegram_id} about {message_count} new emails")

            # In a real implementation, you would:
            # 1. Get the bot instance (passed during initialization)
            # 2. Send a notification message to the user
            # 3. Include a preview of the new emails
            # 4. Add inline buttons to view messages

        except Exception as e:
            logger.error(f"Error sending new email notification: {e}")

    async def _perform_cleanup_tasks(self):
        """
        Perform various cleanup tasks
        """
        try:
            logger.info("Starting cleanup tasks")

            cleanup_stats = {
                'expired_users': 0,
                'temp_files': 0,
                'old_logs': 0
            }

            # Clean up expired users
            expired_count = await self.mongo_client.delete_expired_users()
            cleanup_stats['expired_users'] = expired_count

            # Clean up temporary files
            temp_files_count = await self.email_parser.cleanup_temp_files()
            cleanup_stats['temp_files'] = temp_files_count

            # Additional cleanup tasks can be added here
            # - Clean up old logs
            # - Clean up cached data
            # - Optimize database indexes

            self.stats['last_cleanup_time'] = datetime.utcnow()

            logger.info(f"Cleanup completed: {cleanup_stats}")

            if MONITORING_ENABLED:
                await self._log_cleanup_statistics(cleanup_stats)

        except Exception as e:
            logger.error(f"Error in _perform_cleanup_tasks: {e}")
            self.stats['errors_encountered'] += 1

    async def _log_fetch_statistics(self, user_count: int):
        """
        Log email fetching statistics for monitoring
        """
        try:
            logger.info(
                f"Email fetch stats - Users checked: {user_count}, "
                f"Emails processed: {self.stats['emails_processed']}, "
                f"Attachments processed: {self.stats['attachments_processed']}, "
                f"Errors: {self.stats['errors_encountered']}"
            )
        except Exception as e:
            logger.error(f"Error logging fetch statistics: {e}")

    async def _log_cleanup_statistics(self, cleanup_stats: Dict[str, int]):
        """
        Log cleanup statistics for monitoring
        """
        try:
            logger.info(
                f"Cleanup stats - Expired users: {cleanup_stats['expired_users']}, "
                f"Temp files: {cleanup_stats['temp_files']}, "
                f"Old logs: {cleanup_stats['old_logs']}"
            )
        except Exception as e:
            logger.error(f"Error logging cleanup statistics: {e}")

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get background task statistics
        Returns statistics dictionary
        """
        try:
            # Get current active user count
            active_users = await self.mongo_client.get_all_active_users()

            stats = {
                'tasks_running': self.stats['tasks_running'],
                'active_users': len(active_users),
                'emails_processed': self.stats['emails_processed'],
                'attachments_processed': self.stats['attachments_processed'],
                'errors_encountered': self.stats['errors_encountered'],
                'last_fetch_time': self.stats['last_fetch_time'],
                'last_cleanup_time': self.stats['last_cleanup_time'],
                'uptime': datetime.utcnow() - getattr(self, 'start_time', datetime.utcnow())
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting background task statistics: {e}")
            return {
                'error': 'Failed to get statistics',
                'tasks_running': self.stats['tasks_running']
            }

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on background tasks
        Returns health status dictionary
        """
        try:
            health_status = {
                'status': 'healthy',
                'tasks_running': self.stats['tasks_running'],
                'issues': []
            }

            # Check if tasks are running
            if self.stats['tasks_running'] == 0 and self.running:
                health_status['status'] = 'warning'
                health_status['issues'].append('No background tasks are running')

            # Check IMAP connection
            imap_health = await self.imap_client.test_connection()
            if imap_health.get('status') != 'success':
                health_status['status'] = 'unhealthy'
                health_status['issues'].append('IMAP connection failed')

            # Check MongoDB connection
            mongo_health = await self.mongo_client.health_check()
            if mongo_health.get('status') != 'healthy':
                health_status['status'] = 'unhealthy'
                health_status['issues'].append('MongoDB connection failed')

            # Check error rate
            if self.stats['errors_encountered'] > 10:  # Threshold for too many errors
                health_status['status'] = 'warning'
                health_status['issues'].append('High error rate detected')

            return health_status

        except Exception as e:
            logger.error(f"Error in background tasks health check: {e}")
            return {
                'status': 'unhealthy',
                'issues': [f'Health check error: {str(e)}']
            }

    async def force_email_check(self, telegram_id: int) -> bool:
        """
        Force an immediate email check for a specific user
        Returns True if successful, False otherwise
        """
        try:
            # Get user data
            user_data = await self.mongo_client.get_user(telegram_id)
            if not user_data:
                logger.warning(f"User {telegram_id} not found for force email check")
                return False

            # Ensure IMAP connection
            if not await self.imap_client.ensure_connection():
                logger.error("IMAP connection failed for force email check")
                return False

            # Fetch emails for user
            await self._fetch_emails_for_user(user_data)

            logger.info(f"Force email check completed for user {telegram_id}")
            return True

        except Exception as e:
            logger.error(f"Error in force_email_check for user {telegram_id}: {e}")
            return False

    async def schedule_immediate_task(self, task_func, *args, **kwargs):
        """
        Schedule an immediate background task
        Returns task object
        """
        try:
            task = asyncio.create_task(task_func(*args, **kwargs))
            return task
        except Exception as e:
            logger.error(f"Error scheduling immediate task: {e}")
            return None

    def reset_statistics(self):
        """
        Reset background task statistics
        """
        self.stats = {
            'emails_processed': 0,
            'attachments_processed': 0,
            'errors_encountered': 0,
            'last_fetch_time': None,
            'last_cleanup_time': None,
            'tasks_running': self.stats['tasks_running']  # Keep current running count
        }
        logger.info("Background task statistics reset")

    def get_task_status(self) -> Dict[str, Any]:
        """
        Get current task status
        Returns task status dictionary
        """
        return {
            'running': self.running,
            'tasks_running': self.stats['tasks_running'],
            'fetch_interval': BACKGROUND_FETCH_INTERVAL,
            'cleanup_interval': CLEANUP_INTERVAL,
            'notifications_enabled': NEW_EMAIL_NOTIFICATIONS_ENABLED
        }