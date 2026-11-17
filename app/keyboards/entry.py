"""Inline keyboards and callback data of the expense/income flow."""
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.core.money import format_amount
from app.db.models import Category
from app.i18n import t
from app.services.categories import category_label


class CatCb(CallbackData, prefix="cat"):
    token: str
    category_id: int


class CancelCb(CallbackData, prefix="cx"):
    token: str


class PickCb(CallbackData, prefix="pick"):
    token: str
    index: int


class LargeOkCb(CallbackData, prefix="big"):
    token: str


class UndoCb(CallbackData, prefix="undo"):
    transaction_id: int


class DebtStartCb(CallbackData, prefix="ds"):
    token: str


def _cancel_button(token: str, lang: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=t(lang, "btn.cancel"), callback_data=CancelCb(token=token).pack())


def category_keyboard(
    token: str, categories: list[Category], lang: str, with_debt: bool = False
) -> InlineKeyboardMarkup:
    """Categories two per row (built from the database), Cancel on its own row."""
    buttons = [
        InlineKeyboardButton(
            text=category_label(lang, c.name_key, c.name, c.emoji),
            callback_data=CatCb(token=token, category_id=c.id).pack(),
        )
        for c in categories
    ]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    if with_debt:  # only under expenses: income can never be a debt
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "debt.btn"), callback_data=DebtStartCb(token=token).pack()
                )
            ]
        )
    rows.append([_cancel_button(token, lang)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def amount_keyboard(token: str, candidates: list[dict], lang: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=format_amount(c["amount"], c["currency"]),
                callback_data=PickCb(token=token, index=index).pack(),
            )
        ]
        for index, c in enumerate(candidates)
    ]
    rows.append([_cancel_button(token, lang)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def large_amount_keyboard(token: str, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "btn.large_ok"), callback_data=LargeOkCb(token=token).pack()
                ),
                _cancel_button(token, lang),
            ]
        ]
    )


def undo_keyboard(transaction_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "btn.undo"),
                    callback_data=UndoCb(transaction_id=transaction_id).pack(),
                )
            ]
        ]
    )
