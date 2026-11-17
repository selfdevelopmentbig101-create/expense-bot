"""Inline keyboards and callback data of the debt flow and the /debts screens."""
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.core.debts import DebtKind
from app.db.models import Person
from app.i18n import t
from app.keyboards.entry import CancelCb
from app.services.debts import PersonBalance

MAX_LIST_BUTTONS = 30


class DKindCb(CallbackData, prefix="dk"):
    token: str
    kind: str


class DPersonCb(CallbackData, prefix="dp"):
    token: str
    person_id: int


class DNewPersonCb(CallbackData, prefix="dn"):
    token: str


class DDueCb(CallbackData, prefix="dd"):
    token: str
    choice: str  # none | w1 | m1 | pick


class DConfirmCb(CallbackData, prefix="dc"):
    token: str
    mode: str  # debt = record as a new debt, force = record the overpayment


class DFullCb(CallbackData, prefix="df"):
    token: str


class DUndoCb(CallbackData, prefix="dud"):
    entry_id: int


class PersonCb(CallbackData, prefix="pr"):
    person_id: int


class PActCb(CallbackData, prefix="pa"):
    person_id: int
    currency: str
    action: str  # rep | due | close


class PCloseOkCb(CallbackData, prefix="pc"):
    person_id: int
    currency: str


class PDelCb(CallbackData, prefix="pdl"):
    person_id: int


class PDelOkCb(CallbackData, prefix="pdo"):
    person_id: int


class DebtsListCb(CallbackData, prefix="dl"):
    pass


def _button(text: str, data: CallbackData) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data.pack())


def _cancel(token: str, lang: str) -> list[InlineKeyboardButton]:
    return [_button(t(lang, "btn.cancel"), CancelCb(token=token))]


def _short(name: str, limit: int = 28) -> str:
    return name if len(name) <= limit else name[: limit - 1] + "\u2026"


def _pairs(buttons: list[InlineKeyboardButton]) -> list[list[InlineKeyboardButton]]:
    return [buttons[i : i + 2] for i in range(0, len(buttons), 2)]


# ------------------------------------------------------------------ the flow
def kind_keyboard(token: str, lang: str) -> InlineKeyboardMarkup:
    def kind(k: DebtKind) -> InlineKeyboardButton:
        return _button(t(lang, f"debt.kind.{k.value}"), DKindCb(token=token, kind=k.value))

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [kind(DebtKind.BORROWED), kind(DebtKind.LENT)],
            [kind(DebtKind.REPAID_BY_ME), kind(DebtKind.REPAID_TO_ME)],
            _cancel(token, lang),
        ]
    )


def person_choice_keyboard(token: str, persons: list[Person], lang: str) -> InlineKeyboardMarkup:
    """The most recent people (up to 6) and "New person"."""
    buttons = [
        _button(f"\U0001F464 {_short(p.name)}", DPersonCb(token=token, person_id=p.id))
        for p in persons
    ]
    rows = _pairs(buttons)
    rows.append([_button(t(lang, "debt.person.new"), DNewPersonCb(token=token))])
    rows.append(_cancel(token, lang))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def due_keyboard(token: str, lang: str) -> InlineKeyboardMarkup:
    def due(choice: str) -> InlineKeyboardButton:
        return _button(t(lang, f"debt.due.{choice}"), DDueCb(token=token, choice=choice))

    return InlineKeyboardMarkup(
        inline_keyboard=[[due("none"), due("w1")], [due("m1"), due("pick")], _cancel(token, lang)]
    )


def cancel_keyboard(token: str, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[_cancel(token, lang)])


def confirm_keyboard(token: str, mode: str, lang: str) -> InlineKeyboardMarkup:
    label = t(lang, "debt.btn.as_debt" if mode == "debt" else "debt.btn.anyway")
    return InlineKeyboardMarkup(
        inline_keyboard=[[_button(label, DConfirmCb(token=token, mode=mode))], _cancel(token, lang)]
    )


def repay_keyboard(token: str, full_label: str, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[_button(full_label, DFullCb(token=token))], _cancel(token, lang)]
    )


def debt_undo_keyboard(entry_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[_button(t(lang, "btn.undo"), DUndoCb(entry_id=entry_id))]]
    )


# ------------------------------------------------------------- /debts screens
def debts_list_keyboard(overview: list[PersonBalance]) -> InlineKeyboardMarkup:
    buttons = [
        _button(f"\U0001F464 {_short(p.name)}", PersonCb(person_id=p.person_id))
        for p in overview[:MAX_LIST_BUTTONS]
    ]
    return InlineKeyboardMarkup(inline_keyboard=_pairs(buttons))


def person_actions_keyboard(
    person_id: int, open_balances: dict[str, int], lang: str
) -> InlineKeyboardMarkup:
    """Per open currency: repay, due date, close. Then delete and back."""
    rows = []
    several = len(open_balances) > 1
    for currency in sorted(open_balances):
        suffix = f" {currency}" if several else ""
        repay_key = "debt.kind.repaid_by_me" if open_balances[currency] < 0 else "debt.kind.repaid_to_me"
        rows.append([_button(t(lang, repay_key) + suffix, PActCb(person_id=person_id, currency=currency, action="rep"))])
        rows.append(
            [
                _button(t(lang, "debt.btn.due") + suffix, PActCb(person_id=person_id, currency=currency, action="due")),
                _button(t(lang, "debt.btn.close") + suffix, PActCb(person_id=person_id, currency=currency, action="close")),
            ]
        )
    rows.append([_button(t(lang, "debt.btn.delete"), PDelCb(person_id=person_id))])
    rows.append([_button(t(lang, "btn.back"), DebtsListCb())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def close_confirm_keyboard(person_id: int, currency: str, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_button(t(lang, "debt.btn.close_yes"), PCloseOkCb(person_id=person_id, currency=currency))],
            [_button(t(lang, "btn.back"), PersonCb(person_id=person_id))],
        ]
    )


def delete_confirm_keyboard(person_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [_button(t(lang, "debt.btn.delete_yes"), PDelOkCb(person_id=person_id))],
            [_button(t(lang, "btn.back"), PersonCb(person_id=person_id))],
        ]
    )


def back_to_list_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[_button(t(lang, "btn.back"), DebtsListCb())]])
