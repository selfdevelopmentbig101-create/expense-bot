"""Keyboards of /history and /categories."""
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.db.models import Category
from app.i18n import t
from app.services.categories import category_label
from app.services.history import HistoryItem

MAX_CATEGORY_BUTTONS = 40


class HDelCb(CallbackData, prefix="hd"):
    kind: str  # t = income/expense record, d = debt entry
    record_id: int


class CatMenuCb(CallbackData, prefix="cm"):
    category_id: int


class CatAddCb(CallbackData, prefix="ca"):
    entry_type: str  # expense | income


class CatRenameCb(CallbackData, prefix="cr"):
    category_id: int


class CatRemoveCb(CallbackData, prefix="cd"):
    category_id: int


class CatRemoveOkCb(CallbackData, prefix="cdo"):
    category_id: int


class CatListCb(CallbackData, prefix="cl"):
    pass


def _button(text: str, data: CallbackData) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data.pack())


def history_keyboard(items: list[HistoryItem]) -> InlineKeyboardMarkup:
    """One delete button per record, numbered like the lines of the message."""
    buttons = [
        _button(f"\U0001F5D1 {number}", HDelCb(kind=item.kind, record_id=item.id))
        for number, item in enumerate(items, start=1)
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons[i : i + 5] for i in range(0, len(buttons), 5)])


def categories_keyboard(own: list[Category], lang: str) -> InlineKeyboardMarkup:
    rows = [
        [
            _button(t(lang, "category.btn.add_expense"), CatAddCb(entry_type="expense")),
            _button(t(lang, "category.btn.add_income"), CatAddCb(entry_type="income")),
        ]
    ]
    buttons = [
        _button(category_label(lang, c.name_key, c.name, c.emoji), CatMenuCb(category_id=c.id))
        for c in own[:MAX_CATEGORY_BUTTONS]
    ]
    rows += [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def category_menu_keyboard(category_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                _button(t(lang, "category.btn.rename"), CatRenameCb(category_id=category_id)),
                _button(t(lang, "category.btn.remove"), CatRemoveCb(category_id=category_id)),
            ],
            [_button(t(lang, "btn.back"), CatListCb())],
        ]
    )


def remove_confirm_keyboard(category_id: int, used: bool, lang: str) -> InlineKeyboardMarkup:
    label = t(lang, "category.btn.hide_yes" if used else "category.btn.delete_yes")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_button(label, CatRemoveOkCb(category_id=category_id))],
            [_button(t(lang, "btn.back"), CatMenuCb(category_id=category_id))],
        ]
    )


def back_to_categories_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[_button(t(lang, "btn.back"), CatListCb())]])
