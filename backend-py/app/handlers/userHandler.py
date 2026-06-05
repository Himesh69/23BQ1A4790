from fastapi import HTTPException

from src.logger import get_logger
from app.models import User, UserCreate, UserUpdate
from app.service import user_service


async def get_user_handler(user_id: str) -> User:
    logger = get_logger()

    try:
        await logger.info("handler", "GET /users/:id handler invoked", {
            "additionalContext": {"userId": user_id}
        })

        if not user_id:
            await logger.warn("handler", "Missing required parameter: userId")
            raise HTTPException(status_code=400, detail="User ID is required")

        user = await user_service.get_user_by_id(user_id)

        if not user:
            await logger.warn("handler", "User not found for requested ID", {
                "additionalContext": {"userId": user_id}
            })
            raise HTTPException(status_code=404, detail="User not found")

        await logger.debug("handler", "Returning user data successfully", {
            "additionalContext": {"userId": user_id, "email": user.email}
        })

        return user

    except HTTPException:
        raise
    except Exception as e:
        await logger.error("handler", f"Error in get_user_handler: {str(e)}", {
            "additionalContext": {"userId": user_id}
        })
        raise HTTPException(status_code=500, detail="Internal server error")


async def create_user_handler(user_data: UserCreate) -> User:
    logger = get_logger()

    try:
        await logger.info("handler", "POST /users handler invoked", {
            "additionalContext": {"email": user_data.email}
        })

        # type validation
        if not isinstance(user_data.active, bool):
            await logger.error(
                "handler",
                "Received non-boolean value for active field, expected boolean",
                {
                    "additionalContext": {
                        "received": type(user_data.active).__name__,
                        "value": user_data.active
                    }
                }
            )
            raise HTTPException(
                status_code=400,
                detail="active field must be a boolean"
            )

        new_user = await user_service.create_user(user_data)

        await logger.info("handler", "User created successfully in handler", {
            "additionalContext": {
                "userId": new_user.id,
                "email": new_user.email
            }
        })

        return new_user

    except HTTPException:
        raise
    except Exception as e:
        await logger.error("handler", f"Error in create_user_handler: {str(e)}", {
            "additionalContext": {"email": user_data.email}
        })
        raise HTTPException(status_code=500, detail="Internal server error")


async def list_users_handler() -> list[User]:
    logger = get_logger()

    try:
        await logger.info("handler", "GET /users handler invoked")

        users = await user_service.list_users()

        await logger.debug("handler", "Returning users list", {
            "additionalContext": {"count": len(users)}
        })

        return users

    except Exception as e:
        await logger.error("handler", f"Error in list_users_handler: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def update_user_handler(user_id: str, updates: UserUpdate) -> User:
    logger = get_logger()

    try:
        update_dict = updates.model_dump(exclude_unset=True)
        await logger.info("handler", "PUT /users/:id handler invoked", {
            "additionalContext": {
                "userId": user_id,
                "updatingFields": list(update_dict.keys())
            }
        })

        if not user_id:
            await logger.warn("handler", "Missing required parameter: userId")
            raise HTTPException(status_code=400, detail="User ID is required")

        updated_user = await user_service.update_user(user_id, updates)

        await logger.info("handler", "User updated successfully", {
            "additionalContext": {
                "userId": user_id,
                "updatedFields": list(update_dict.keys())
            }
        })

        return updated_user

    except HTTPException:
        raise
    except Exception as e:
        await logger.error("handler", f"Error in update_user_handler: {str(e)}", {
            "additionalContext": {"userId": user_id}
        })
        raise HTTPException(status_code=500, detail="Internal server error")
