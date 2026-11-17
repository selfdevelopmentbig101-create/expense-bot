"""Small helpers shared by handlers."""
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from app.core.parser import ParseError

# Parser error -> translation key (MULTIPLE_AMOUNTS has its own buttons)
AMOUNT_ERROR_KEYS = {
    ParseError.NO_AMOUNT: "amount.help",
    ParseError.INVALID_AMOUNT: "amount.help",
    ParseError.ZERO_AMOUNT: "amount.zero",
    ParseError.TOO_MANY_DECIMALS: "amount.decimals",
    ParseError.TOO_LARGE: "amount.too_large",
}


async def safe_edit(
    callback: CallbackQuery, text: str, reply_markup: InlineKeyboardMarkup | None = None
) -> None:
    """Edit the message under a pressed button. Ignores "message is not modified"."""
    if not isinstance(callback.message, Message):
        return
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc):
            raise
