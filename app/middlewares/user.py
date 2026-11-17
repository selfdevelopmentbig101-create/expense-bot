"""Creates the user row on first contact and passes `user` to handlers."""
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.services.users import get_or_create_user


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        if tg_user is None or tg_user.is_bot:
            return None  # updates without a human sender are ignored

        chat = data.get("event_chat")
        if chat is not None and chat.type != "private":
            return None  # the bot is for private chats only

        user, is_new = await get_or_create_user(
            data["session"], tg_user.id, tg_user.language_code
        )
        data["user"] = user
        data["is_new_user"] = is_new
        return await handler(event, data)
