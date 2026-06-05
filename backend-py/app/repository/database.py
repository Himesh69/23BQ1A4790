from datetime import datetime
from typing import Optional

from src.logger import get_logger
from app.models import User, UserCreate, UserUpdate


class DatabaseService:

    def __init__(self):
        self.is_connected = False
        self.users: dict[str, User] = {}

    async def connect(self) -> None:
        logger = get_logger()

        try:
            await logger.info("db", "Attempting to establish database connection", {
                "additionalContext": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "appdb"
                }
            })

            import asyncio
            await asyncio.sleep(0.5)

            self.is_connected = True

            await logger.info("db", "Database connection established successfully", {
                "additionalContext": {"connectionTime": "500ms"}
            })

        except Exception as e:
            await logger.fatal("db", f"Critical database connection failure: {str(e)}")
            raise

    async def disconnect(self) -> None:
        logger = get_logger()

        try:
            if not self.is_connected:
                await logger.warn("db", "Attempted to disconnect when not connected")
                return

            self.is_connected = False
            await logger.info("db", "Database disconnected gracefully")

        except Exception as e:
            await logger.error("db", f"Error during database disconnect: {str(e)}")

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        logger = get_logger()

        try:
            await logger.debug("db", "Fetching user from database", {
                "additionalContext": {"userId": user_id}
            })

            user = self.users.get(user_id)

            if not user:
                await logger.warn("db", "User not found in database", {
                    "additionalContext": {"userId": user_id}
                })
                return None

            await logger.debug("db", "User retrieved successfully", {
                "additionalContext": {"userId": user_id, "email": user.email}
            })

            return user

        except Exception as e:
            await logger.error("db", f"Error fetching user by ID: {str(e)}", {
                "additionalContext": {"userId": user_id}
            })
            raise

    async def create_user(self, user_data: UserCreate) -> User:
        logger = get_logger()

        try:
            if not isinstance(user_data.active, bool):
                await logger.error(
                    "db",
                    f"Received non-boolean value for active field, expected boolean",
                    {
                        "additionalContext": {
                            "received": type(user_data.active).__name__,
                            "value": user_data.active
                        }
                    }
                )
                raise TypeError("active field must be boolean")

            new_user = User(
                id=f"user-{datetime.utcnow().timestamp()}",
                email=user_data.email,
                name=user_data.name,
                active=user_data.active,
                createdAt=datetime.utcnow()
            )

            self.users[new_user.id] = new_user

            await logger.info("db", "New user created in database", {
                "additionalContext": {
                    "userId": new_user.id,
                    "email": new_user.email,
                    "timestamp": new_user.createdAt.isoformat()
                }
            })

            return new_user

        except Exception as e:
            await logger.error("db", f"Error creating user: {str(e)}", {
                "additionalContext": {"email": user_data.email}
            })
            raise

    async def update_user(self, user_id: str, updates: UserUpdate) -> User:
        logger = get_logger()

        try:
            user = self.users.get(user_id)

            if not user:
                await logger.warn("db", "Attempted to update non-existent user", {
                    "additionalContext": {"userId": user_id}
                })
                raise ValueError("User not found")

            update_data = updates.model_dump(exclude_unset=True)
            updated_user = user.model_copy(update=update_data)
            self.users[user_id] = updated_user

            await logger.info("db", "User updated successfully", {
                "additionalContext": {
                    "userId": user_id,
                    "updatedFields": list(update_data.keys())
                }
            })

            return updated_user

        except Exception as e:
            await logger.error("db", f"Error updating user: {str(e)}", {
                "additionalContext": {"userId": user_id}
            })
            raise

    async def list_all_users(self) -> list[User]:
        logger = get_logger()

        try:
            users = list(self.users.values())

            await logger.debug("db", "Retrieved all users from database", {
                "additionalContext": {"count": len(users)}
            })

            return users

        except Exception as e:
            await logger.error("db", f"Error listing users: {str(e)}")
            raise


db_service = DatabaseService()
