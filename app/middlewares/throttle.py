"""Rate limiting: a user who floods the bot is ignored for a few seconds."""
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramAPIError
from aiogram.types import TelegramObject

from app.core.ratelimit import RateLimiter
from app.i18n import detect_language, t

logger = logging.getLogger(__name__)


class ThrottleMiddleware(BaseMiddleware):
    """Messages: 15 per 10 seconds. Button taps: 30 per 10 seconds (taps are quick, and double
    taps are already harmless). Everything above that is dropped."""

    def __init__(
        self,
        message_limit: int = 15,
        callback_limit: int = 30,
        window: float = 10.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.messages = RateLimiter(message_limit, window)
        self.callbacks = RateLimiter(callback_limit, window)
        self.clock = clock

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        callback = getattr(event, "callback_query", None)
        message = getattr(event, "message", None)
        if tg_user is None or (callback is None and message is None):
            return await handler(event, data)

        limiter = self.callbacks if callback is not None else self.messages
        decision = limiter.check(tg_user.id, self.clock())
        if decision.allowed:
            return await handler(event, data)

        logger.info("Rate limit: dropped an update from %s", tg_user.id)
        bot = data["bot"]
        text = t(detect_language(tg_user.language_code), "throttle.slow_down")
        try:
            if callback is not None:  # always answer, or the button keeps spinning
                await bot.answer_callback_query(callback.id, text=text if decision.warn else None)
            elif decision.warn:
                await bot.send_message(message.chat.id, text)
        except TelegramAPIError:
            logger.debug("Could not send the slow-down notice", exc_info=True)
        return None
