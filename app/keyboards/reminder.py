"""Buttons under an overdue-debt reminder."""
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n import t


class RemCb(CallbackData, prefix="rm"):
    person_id: int
    currency: str
    action: str  # ok = repaid, snz = postpone


def overdue_keyboard(person_id: int, currency: str, lang: str) -> InlineKeyboardMarkup:
    def button(key: str, action: str) -> InlineKeyboardButton:
        data = RemCb(person_id=person_id, currency=currency, action=action)
        return InlineKeyboardButton(text=t(lang, key), callback_data=data.pack())

    return InlineKeyboardMarkup(
        inline_keyboard=[[button("reminder.btn.repaid", "ok"), button("reminder.btn.postpone", "snz")]]
    )
