"""
MongoDB client for Telegram Temp Mail Bot
Handles all database operations for user data storage
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import ConnectionFailure, DuplicateKeyError, OperationFailure
from pymongo import ReturnDocument

from config import (
    MONGO_CONNECTION_STRING,
    MONGO_DATABASE_NAME,
    MONGO_COLLECTION_NAME,
    MONGO_MAX_POOL_SIZE,
    MONGO_SERVER_SELECTION_TIMEOUT,
    MONGO_CONNECT_TIMEOUT,
    EMAIL_EXPIRY_TIME
)

logger = logging.getLogger(__name__)


class MongoDBClient:
    """Async MongoDB client for Temp Mail Bot"""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.collection: Optional[AsyncIOMotorCollection] = None
        self.connected = False

    async def connect(self) -> bool:
        """
        Connect to MongoDB and setup collections with indexes
        Returns True if connection successful, False otherwise
        """
        try:
            logger.info("Connecting to MongoDB...")

            # Create MongoDB client with connection options
            self.client = AsyncIOMotorClient(
                MONGO_CONNECTION_STRING,
                maxPoolSize=MONGO_MAX_POOL_SIZE,
                serverSelectionTimeoutMS=MONGO_SERVER_SELECTION_TIMEOUT,
                connectTimeoutMS=MONGO_CONNECT_TIMEOUT,
                retryWrites=True,
                w="majority"
            )

            # Test the connection
            await self.client.admin.command('ping')

            # Get database and collection
            self.database = self.client[MONGO_DATABASE_NAME]
            self.collection = self.database[MONGO_COLLECTION_NAME]

            # Create indexes for optimal performance
            await self._create_indexes()

            self.connected = True
            logger.info("Successfully connected to MongoDB")
            return True

        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            self.connected = False
            return False

    async def _create_indexes(self):
        """Create necessary indexes for the collection"""
        try:
            # Unique index on telegram_id
            await self.collection.create_index(
                "telegram_id",
                unique=True,
                background=True
            )

            # Index on expires_at for efficient cleanup queries
            await self.collection.create_index(
                "expires_at",
                background=True
            )

            # Index on email for quick lookups
            await self.collection.create_index(
                "email",
                background=True
            )

            # Compound index for active users with expiry check
            await self.collection.create_index(
                [("is_active", 1), ("expires_at", 1)],
                background=True
            )

            logger.info("MongoDB indexes created successfully")

        except OperationFailure as e:
            logger.error(f"Failed to create indexes: {e}")
            raise

    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("MongoDB connection closed")

    async def create_user(self, telegram_id: int, email: str, prefix: str = None) -> Dict[str, Any]:
        """
        Create a new user with temporary email
        Returns the created user document
        """
        if not self.connected:
            raise ConnectionError("MongoDB not connected")

        try:
            # Deactivate existing user if any
            await self.deactivate_user(telegram_id)

            # Calculate expiry time
            created_at = datetime.utcnow()
            expires_at = created_at + EMAIL_EXPIRY_TIME

            # Create user document
            user_doc = {
                "telegram_id": telegram_id,
                "email": email,
                "prefix": prefix or email.split('@')[0].split('_')[0],
                "created_at": created_at,
                "expires_at": expires_at,
                "is_active": True,
                "last_checked": created_at,
                "message_count": 0,
                "total_messages_received": 0,
                "last_message_date": None
            }

            # Insert into database
            result = await self.collection.insert_one(user_doc)
            user_doc["_id"] = result.inserted_id

            logger.info(f"Created new user: telegram_id={telegram_id}, email={email}")
            return user_doc

        except DuplicateKeyError:
            logger.error(f"User with telegram_id {telegram_id} already exists")
            raise ValueError("User already exists")
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    async def get_user(self, telegram_id: int, active_only: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get user by telegram_id
        Returns user document or None if not found
        """
        if not self.connected:
            raise ConnectionError("MongoDB not connected")

        try:
            query = {"telegram_id": telegram_id}
            if active_only:
                query["is_active"] = True

            user = await self.collection.find_one(query)
            return user

        except Exception as e:
            logger.error(f"Error getting user {telegram_id}: {e}")
            raise

    async def get_user_by_email(self, email: str, active_only: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get user by email address
        Returns user document or None if not found
        """
        if not self.connected:
            raise ConnectionError("MongoDB not connected")

        try:
            query = {"email": email}
            if active_only:
                query["is_active"] = True

            user = await self.collection.find_one(query)
            return user

        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise

    async def update_last_checked(self, telegram_id: int) -> bool:
        """
        Update the last_checked timestamp for a user
        Returns True if successful, False otherwise
        """
        if not self.connected:
            raise ConnectionError("MongoDB not connected")

        try:
            result = await self.collection.update_one(
                {"telegram_id": telegram_id, "is_active": True},
                {"$set": {"last_checked": datetime.utcnow()}}
            )

            success = result.modified_count > 0
            if success:
                logger.debug(f"Updated last_checked for user {telegram_id}")

            return success

        except Exception as e:
            logger.error(f"Error updating last_checked for user {telegram_id}: {e}")
            return False

    async def increment_message_count(self, telegram_id: int) -> bool:
        """
        Increment message count and update last_message_date
        Returns True if successful, False otherwise
        """
        if not self.connected:
            raise ConnectionError("MongoDB not connected")

        try:
            now = datetime.utcnow()
            result = await self.collection.update_one(
                {"telegram_id": telegram_id, "is_active": True},
                {
                    "$inc": {
                        "message_count": 1,
                        "total_messages_received": 1
                    },
                    "$set": {"last_message_date": now}
                }
            )

            success = result.modified_count > 0
            if success:
                logger.debug(f"Incremented message count for user {telegram_id}")

            return success

        except Exception as e:
            logger.error(f"Error incrementing message count for user {telegram_id}: {e}")
            return False

    async def deactivate_user(self, telegram_id: int) -> bool:
        """
        Deactivate user (soft delete)
        Returns True if successful, False otherwise
        """
        if not self.connected:
            raise ConnectionError("MongoDB not connected")

        try:
            result = await self.collection.update_one(
                {"telegram_id": telegram_id, "is_active": True},
                {"$set": {"is_active": False, "deactivated_at": datetime.utcnow()}}
            )

            success = result.modified_count > 0
            if success:
                logger.info(f"Deactivated user {telegram_id}")

            return success

        except Exception as e:
            logger.error(f"Error deactivating user {telegram_id}: {e}")
            return False

    async def delete_user(self, telegram_id: int) -> bool:
        """
        Permanently delete user from database
        Returns True if successful, False otherwise
        """
        if not self.connected:
            raise ConnectionError("MongoDB not connected")

        try:
            result = await self.collection.delete_one({"telegram_id": telegram_id})

            success = result.deleted_count > 0
            if success:
                logger.info(f"Deleted user {telegram_id}")

            return success

        except Exception as e:
            logger.error(f"Error deleting user {telegram_id}: {e}")
            return False

    async def delete_expired_users(self) -> int:
        """
        Deactivate all expired users
        Returns number of users deactivated
        """
        if not self.connected:
            raise ConnectionError("MongoDB not connected")

        try:
            now = datetime.utcnow()
            result = await self.collection.update_many(
                {
                    "is_active": True,
                    "expires_at": {"$lt": now}
                },
                {
                    "$set": {
                        "is_active": False,
                        "deactivated_at": now,
                        "deactivation_reason": "expired"
                    }
                }
            )

            count = result.modified_count
            if count > 0:
                logger.info(f"Deactivated {count} expired users")

            return count

        except Exception as e:
            logger.error(f"Error deleting expired users: {e}")
            return 0

    async def get_all_active_users(self) -> List[Dict[str, Any]]:
        """
        Get all active users
        Returns list of user documents
        """
        if not self.connected:
            raise ConnectionError("MongoDB not connected")

        try:
            cursor = self.collection.find({"is_active": True})
            users = await cursor.to_list(length=None)
            return users

        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []

    async def get_users_expiring_soon(self, hours: int = 1) -> List[Dict[str, Any]]:
        """
        Get users whose emails will expire within the specified hours
        Returns list of user documents
        """
        if not self.connected:
            raise ConnectionError("MongoDB not connected")

        try:
            threshold = datetime.utcnow() + timedelta(hours=hours)
            cursor = self.collection.find({
                "is_active": True,
                "expires_at": {"$lt": threshold}
            })
            users = await cursor.to_list(length=None)
            return users

        except Exception as e:
            logger.error(f"Error getting users expiring soon: {e}")
            return []

    async def get_user_statistics(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a specific user
        Returns statistics dictionary or None if user not found
        """
        if not self.connected:
            raise ConnectionError("MongoDB not connected")

        try:
            user = await self.get_user(telegram_id, active_only=False)
            if not user:
                return None

            now = datetime.utcnow()
            time_remaining = None
            if user.get("is_active") and user.get("expires_at"):
                time_remaining = user["expires_at"] - now
                if time_remaining.total_seconds() < 0:
                    time_remaining = timedelta(0)

            stats = {
                "email": user.get("email"),
                "created_at": user.get("created_at"),
                "expires_at": user.get("expires_at"),
                "time_remaining": time_remaining,
                "is_active": user.get("is_active"),
                "message_count": user.get("message_count", 0),
                "total_messages_received": user.get("total_messages_received", 0),
                "last_checked": user.get("last_checked"),
                "last_message_date": user.get("last_message_date")
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return None

    async def cleanup_temp_files(self) -> int:
        """
        Clean up any temporary data or expired sessions
        Returns number of items cleaned up
        """
        if not self.connected:
            raise ConnectionError("MongoDB not connected")

        try:
            # This could be extended to clean up other temporary data
            # For now, just count active vs inactive users
            total_count = await self.collection.count_documents({})
            active_count = await self.collection.count_documents({"is_active": True})
            inactive_count = total_count - active_count

            logger.info(f"Database stats - Total: {total_count}, Active: {active_count}, Inactive: {inactive_count}")

            # Could add cleanup logic here for very old inactive users
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            result = await self.collection.delete_many({
                "is_active": False,
                "deactivated_at": {"$lt": cutoff_date}
            })

            if result.deleted_count > 0:
                logger.info(f"Cleaned up {result.deleted_count} old inactive users")

            return result.deleted_count

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on MongoDB connection
        Returns health status dictionary
        """
        try:
            if not self.connected or not self.client:
                return {
                    "status": "unhealthy",
                    "error": "Not connected to MongoDB"
                }

            # Test connection
            await self.client.admin.command('ping')

            # Get basic stats
            stats = await self.database.command("dbStats")

            return {
                "status": "healthy",
                "collections": stats.get("collections", 0),
                "data_size": stats.get("dataSize", 0),
                "indexes": stats.get("indexes", 0)
            }

        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }