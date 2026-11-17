"""Optional allowlist: when ALLOWED_USER_IDS is set, everyone else is refused."""
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramAPIError
from aiogram.types import TelegramObject

from app.i18n import detect_language, t

logger = logging.getLogger(__name__)


class AccessMiddleware(BaseMiddleware):
    def __init__(self, allowed_ids: frozenset[int]) -> None:
        self.allowed_ids = allowed_ids

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        if not self.allowed_ids or tg_user is None or tg_user.id in self.allowed_ids:
            return await handler(event, data)

        logger.warning("Access denied for telegram_id=%s", tg_user.id)
        chat = data.get("event_chat")
        if chat is not None:
            try:
                text = t(detect_language(tg_user.language_code), "access.denied")
                await data["bot"].send_message(chat.id, text)
            except TelegramAPIError:
                logger.info("Could not send the refusal message", exc_info=True)
        return None
