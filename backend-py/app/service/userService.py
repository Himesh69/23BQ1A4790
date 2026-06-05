from src.logger import get_logger
from app.models import User, UserCreate, UserUpdate
from app.repository import db_service
from app.cache import cache_service
from app.config import settings


class UserService:

    async def get_user_by_id(self, user_id: str) -> User | None:
        logger = get_logger()

        try:
            await logger.info("service", "Starting user retrieval operation", {
                "additionalContext": {"userId": user_id}
            })

            cache_key = f"user:{user_id}"
            cached_user = await cache_service.get(cache_key)

            if cached_user:
                await logger.info("service", "User retrieved from cache (avoiding DB query)", {
                    "additionalContext": {
                        "userId": user_id,
                        "source": "cache"
                    }
                })
                return cached_user

            user = await db_service.get_user_by_id(user_id)

            if user:
                await cache_service.set(
                    cache_key, user, settings.CACHE_TTL
                )

                await logger.info("service", "User retrieved and cached successfully", {
                    "additionalContext": {
                        "userId": user_id,
                        "email": user.email,
                        "source": "database"
                    }
                })

            return user

        except Exception as e:
            await logger.error("service", f"Error retrieving user: {str(e)}", {
                "additionalContext": {"userId": user_id}
            })
            raise

    async def create_user(self, user_data: UserCreate) -> User:
        logger = get_logger()

        try:
            await logger.info("service", "Starting user creation process", {
                "additionalContext": {"email": user_data.email}
            })

            if "@" not in user_data.email:
                await logger.warn("service", "Invalid email format provided during user creation", {
                    "additionalContext": {"email": user_data.email}
                })
                raise ValueError("Invalid email format")

            if not isinstance(user_data.active, bool):
                await logger.error(
                    "service",
                    f"Received non-boolean for active field, expected boolean",
                    {
                        "additionalContext": {
                            "received": type(user_data.active).__name__,
                            "expected": "bool"
                        }
                    }
                )
                raise TypeError("active field must be boolean")

            new_user = await db_service.create_user(user_data)

            await logger.info("service", "User created successfully", {
                "additionalContext": {
                    "userId": new_user.id,
                    "email": new_user.email
                }
            })

            return new_user

        except Exception as e:
            await logger.error("service", f"Error creating user: {str(e)}", {
                "additionalContext": {"email": user_data.email}
            })
            raise

    async def update_user(self, user_id: str, updates: UserUpdate) -> User:
        logger = get_logger()

        try:
            update_dict = updates.model_dump(exclude_unset=True)
            await logger.info("service", "Starting user update operation", {
                "additionalContext": {
                    "userId": user_id,
                    "fieldsBeingUpdated": list(update_dict.keys())
                }
            })

            updated_user = await db_service.update_user(user_id, updates)

            # invalidate cache after update
            cache_key = f"user:{user_id}"
            await cache_service.delete(cache_key)

            await logger.info("service", "User updated successfully", {
                "additionalContext": {
                    "userId": user_id,
                    "updatedFields": list(update_dict.keys())
                }
            })

            return updated_user

        except Exception as e:
            await logger.error("service", f"Error updating user: {str(e)}", {
                "additionalContext": {"userId": user_id}
            })
            raise

    async def list_users(self) -> list[User]:
        logger = get_logger()

        try:
            await logger.info("service", "Fetching all users")

            cache_key = "users:all"
            cached_users = await cache_service.get(cache_key)

            if cached_users:
                await logger.debug("service", "Returning users from cache", {
                    "additionalContext": {"count": len(cached_users)}
                })
                return cached_users

            users = await db_service.list_all_users()

            if users:
                await cache_service.set(cache_key, users, settings.CACHE_TTL)

            await logger.info("service", "Users list retrieved", {
                "additionalContext": {"count": len(users)}
            })

            return users

        except Exception as e:
            await logger.error("service", f"Error listing users: {str(e)}")
            raise


user_service = UserService()
