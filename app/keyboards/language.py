"""Language picker keyboard."""
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.i18n import LANGUAGE_NAMES, LANGUAGES


class LangCb(CallbackData, prefix="lang"):
    code: str
    # "start" = picker under the first greeting, "cmd" = opened by /language
    source: str


def language_keyboard(source: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code in LANGUAGES:
        builder.button(text=LANGUAGE_NAMES[code], callback_data=LangCb(code=code, source=source))
    builder.adjust(3)
    return builder.as_markup()
