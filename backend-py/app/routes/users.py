from fastapi import APIRouter

from src.logger import get_logger
from app.models import User, UserCreate, UserUpdate
from app.handlers import (
    get_user_handler,
    create_user_handler,
    list_users_handler,
    update_user_handler,
)

router = APIRouter(prefix="/api/users", tags=["users"])
logger = None

try:
    logger = get_logger()
except RuntimeError:
    pass


@router.get("", response_model=list[User])
async def list_users():
    if logger:
        await logger.info("route", "GET /api/users route accessed")
    return await list_users_handler()


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str):
    if logger:
        await logger.info("route", "GET /api/users/:id route accessed", {
            "additionalContext": {"userId": user_id}
        })
    return await get_user_handler(user_id)


@router.post("", response_model=User, status_code=201)
async def create_user(user: UserCreate):
    if logger:
        await logger.info("route", "POST /api/users route accessed", {
            "additionalContext": {"email": user.email}
        })
    return await create_user_handler(user)


@router.put("/{user_id}", response_model=User)
async def update_user(user_id: str, updates: UserUpdate):
    if logger:
        update_dict = updates.model_dump(exclude_unset=True)
        await logger.info("route", "PUT /api/users/:id route accessed", {
            "additionalContext": {
                "userId": user_id,
                "updates": list(update_dict.keys())
            }
        })
    return await update_user_handler(user_id, updates)
