from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User

from app.db.repositories.users_repo import UsersRepo

log = logging.getLogger(__name__)


class UserMiddleware(BaseMiddleware):
    """Регистрирует/обновляет пользователя при каждом апдейте."""

    def __init__(self, users_repo: UsersRepo) -> None:
        self.users_repo = users_repo

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        if user is not None and not user.is_bot:
            try:
                await self.users_repo.upsert(
                    user_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    language_code=user.language_code,
                )
            except Exception as e:
                log.warning("Failed to upsert user %s: %s", user.id, e)
        return await handler(event, data)
