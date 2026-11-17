"""The safety net: whatever goes wrong, the bot stays up and the user gets a calm answer."""
import logging

from aiogram import Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import ErrorEvent, Update

from app.core.errors import is_benign_telegram_error
from app.i18n import detect_language, t

logger = logging.getLogger(__name__)
router = Router(name="errors")


async def _tell_user(update: Update, text: str | None) -> None:
    """Answer the message or the button press that failed. Never raises."""
    try:
        if update.callback_query is not None:
            await update.callback_query.answer(text, show_alert=bool(text))
        elif update.message is not None and text:
            await update.message.answer(text)
    except Exception:  # the user may have blocked the bot, deleted the chat ...
        logger.debug("Could not tell the user about an error", exc_info=True)


@router.errors()
async def on_error(event: ErrorEvent) -> bool:
    exc, update = event.exception, event.update

    if isinstance(exc, TelegramAPIError) and is_benign_telegram_error(str(exc)):
        logger.info("Ignored a harmless Telegram error: %s", exc)
        await _tell_user(update, None)  # stop the spinner on a button
        return True

    logger.error(
        "Unhandled error while processing update %s",
        update.update_id,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    sender = (update.message or update.callback_query).from_user if (update.message or update.callback_query) else None
    language = detect_language(sender.language_code if sender else None)
    await _tell_user(update, t(language, "error.generic"))
    return True
