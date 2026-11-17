"""Keyboards of /settings."""
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.core.money import SUPPORTED_CURRENCIES
from app.i18n import LANGUAGE_NAMES, LANGUAGES, t
from app.keyboards.language import LangCb

EVENING_CHOICES = ("1900", "2000", "2100", "2200")  # no colon: ':' separates callback fields


class SetOpenCb(CallbackData, prefix="so"):
    section: str  # language | currency | evening


class SetCurrencyCb(CallbackData, prefix="sc"):
    code: str


class SetEveningCb(CallbackData, prefix="se"):
    value: str  # off | other | 1900 ...


class SetDebtCb(CallbackData, prefix="sd"):
    pass


class SetBackCb(CallbackData, prefix="sb"):
    pass


def _button(text: str, data: CallbackData) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data.pack())


def _back(lang: str) -> list[InlineKeyboardButton]:
    return [_button(t(lang, "btn.back"), SetBackCb())]


def settings_keyboard(lang: str, debt_reminders_on: bool) -> InlineKeyboardMarkup:
    state = t(lang, "settings.on" if debt_reminders_on else "settings.off")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_button(t(lang, "settings.btn.language"), SetOpenCb(section="language"))],
            [_button(t(lang, "settings.btn.currency"), SetOpenCb(section="currency"))],
            [_button(t(lang, "settings.btn.evening"), SetOpenCb(section="evening"))],
            [_button(f"{t(lang, 'settings.btn.debt')}: {state}", SetDebtCb())],
        ]
    )


def language_choice_keyboard(lang: str) -> InlineKeyboardMarkup:
    buttons = [
        _button(LANGUAGE_NAMES[code], LangCb(code=code, source="settings")) for code in LANGUAGES
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons, _back(lang)])


def currency_keyboard(lang: str) -> InlineKeyboardMarkup:
    buttons = [_button(code, SetCurrencyCb(code=code)) for code in SUPPORTED_CURRENCIES]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(inline_keyboard=rows + [_back(lang)])


def evening_keyboard(lang: str) -> InlineKeyboardMarkup:
    times = [_button(f"{v[:2]}:{v[2:]}", SetEveningCb(value=v)) for v in EVENING_CHOICES]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            times,
            [
                _button(t(lang, "settings.evening_other"), SetEveningCb(value="other")),
                _button(t(lang, "settings.btn.off"), SetEveningCb(value="off")),
            ],
            _back(lang),
        ]
    )
