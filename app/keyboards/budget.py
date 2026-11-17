"""Keyboards of /budget."""
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.core.money import format_amount
from app.db.models import Category
from app.i18n import t
from app.services.budgets import BudgetProgress
from app.services.categories import category_label


class BudgetAddCb(CallbackData, prefix="ba"):
    pass


class BudgetCatCb(CallbackData, prefix="bc"):
    category_id: int


class BudgetMenuCb(CallbackData, prefix="bm"):
    category_id: int


class BudgetRemoveCb(CallbackData, prefix="br"):
    category_id: int


class BudgetListCb(CallbackData, prefix="bl"):
    pass


def _button(text: str, data: CallbackData) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data.pack())


def _pairs(buttons: list[InlineKeyboardButton]) -> list[list[InlineKeyboardButton]]:
    return [buttons[i : i + 2] for i in range(0, len(buttons), 2)]


def budgets_keyboard(items: list[BudgetProgress], lang: str) -> InlineKeyboardMarkup:
    rows = [[_button(t(lang, "budget.btn.add"), BudgetAddCb())]]
    buttons = [
        _button(
            f"{category_label(lang, i.name_key, i.name, i.emoji)} \u00b7 {format_amount(i.limit, i.currency)}",
            BudgetMenuCb(category_id=i.category_id),
        )
        for i in items
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows + _pairs(buttons))


def category_pick_keyboard(categories: list[Category], lang: str) -> InlineKeyboardMarkup:
    buttons = [
        _button(category_label(lang, c.name_key, c.name, c.emoji), BudgetCatCb(category_id=c.id))
        for c in categories
    ]
    rows = _pairs(buttons) + [[_button(t(lang, "btn.back"), BudgetListCb())]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def budget_menu_keyboard(category_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _button(t(lang, "budget.btn.change"), BudgetCatCb(category_id=category_id)),
                _button(t(lang, "budget.btn.remove"), BudgetRemoveCb(category_id=category_id)),
            ],
            [_button(t(lang, "btn.back"), BudgetListCb())],
        ]
    )
