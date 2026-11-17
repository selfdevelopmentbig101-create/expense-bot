"""/debts: the overview, one person's screen and the actions on it."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.debts import DebtKind
from app.core.money import format_amount
from app.db.models import User
from app.handlers.debt_views import message_ref, overview_screen, person_screen, render_state
from app.handlers.utils import safe_edit
from app.i18n import t
from app.keyboards.debt import (
    DebtsListCb,
    PActCb,
    PCloseOkCb,
    PDelCb,
    PDelOkCb,
    PersonCb,
    back_to_list_keyboard,
    close_confirm_keyboard,
    debt_undo_keyboard,
    delete_confirm_keyboard,
)
from app.services.debt_formatting import esc
from app.services.debts import close_debt, delete_person, get_person, get_person_balances
from app.services.pending import PendingState, create_pending

router = Router(name="debts")


@router.message(Command("debts"))
async def cmd_debts(message: Message, session: AsyncSession, user: User) -> None:
    text, markup = await overview_screen(session, user)
    await message.answer(text, reply_markup=markup)


@router.callback_query(DebtsListCb.filter())
async def on_back_to_list(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    text, markup = await overview_screen(session, user)
    await safe_edit(callback, text, markup)
    await callback.answer()


async def _show_person(callback: CallbackQuery, session: AsyncSession, user: User, person_id: int) -> None:
    screen = await person_screen(session, user, person_id)
    if screen is None:
        await callback.answer(t(user.language, "debt.person.gone"))
        return
    await safe_edit(callback, *screen)
    await callback.answer()


@router.callback_query(PersonCb.filter())
async def on_person_open(
    callback: CallbackQuery, callback_data: PersonCb, session: AsyncSession, user: User
) -> None:
    await _show_person(callback, session, user, callback_data.person_id)


@router.callback_query(PActCb.filter())
async def on_person_action(
    callback: CallbackQuery, callback_data: PActCb, session: AsyncSession, user: User
) -> None:
    lang, currency = user.language, callback_data.currency
    person = await get_person(session, user.id, callback_data.person_id)
    if person is None:
        await callback.answer(t(lang, "debt.person.gone"))
        return
    balance = (await get_person_balances(session, user.id, person.id)).get(currency, 0)
    if balance == 0:  # closed in the meantime
        await callback.answer(t(lang, "debt.nothing"))
        await _show_person(callback, session, user, person.id)
        return

    action = callback_data.action
    if action == "close":
        text = t(
            lang,
            "debt.close.confirm",
            person=esc(person.name),
            amount=format_amount(abs(balance), currency),
        )
        await safe_edit(callback, text, close_confirm_keyboard(person.id, currency, lang))
    elif action in ("rep", "due"):
        base = {
            "flow": "debt",
            "person_id": person.id,
            "person_name": person.name,
            "currency": currency,
            **message_ref(callback),
        }
        if action == "rep":
            kind = DebtKind.REPAID_BY_ME if balance < 0 else DebtKind.REPAID_TO_ME
            payload = {**base, "mode": "person", "kind": kind.value, "owed": abs(balance)}
            state = PendingState.DEBT_REPAY_AMOUNT
        else:
            payload = {**base, "mode": "change_due"}
            state = PendingState.DEBT_DUE
        pending = await create_pending(session, user.id, state, payload)
        text, markup = await render_state(session, user, pending)
        await safe_edit(callback, text, markup)
    await callback.answer()


@router.callback_query(PCloseOkCb.filter())
async def on_close_confirmed(
    callback: CallbackQuery, callback_data: PCloseOkCb, session: AsyncSession, user: User
) -> None:
    lang = user.language
    person = await get_person(session, user.id, callback_data.person_id)
    if person is None:
        await callback.answer(t(lang, "debt.person.gone"))
        return
    entry = await close_debt(
        session,
        user.id,
        person.id,
        callback_data.currency,
        note=t(lang, "debt.close.note"),
    )
    if entry is None:  # already closed (double tap)
        await callback.answer(t(lang, "debt.nothing"))
        return
    text = t(
        lang,
        "debt.close.done",
        person=esc(person.name),
        amount=format_amount(entry.amount, entry.currency),
    )
    await safe_edit(callback, text, debt_undo_keyboard(entry.id, lang))
    await callback.answer()


@router.callback_query(PDelCb.filter())
async def on_delete_person(
    callback: CallbackQuery, callback_data: PDelCb, session: AsyncSession, user: User
) -> None:
    person = await get_person(session, user.id, callback_data.person_id)
    if person is None:
        await callback.answer(t(user.language, "debt.person.gone"))
        return
    text = t(user.language, "debt.delete.confirm", person=esc(person.name))
    await safe_edit(callback, text, delete_confirm_keyboard(person.id, user.language))
    await callback.answer()


@router.callback_query(PDelOkCb.filter())
async def on_delete_confirmed(
    callback: CallbackQuery, callback_data: PDelOkCb, session: AsyncSession, user: User
) -> None:
    person = await get_person(session, user.id, callback_data.person_id)
    if person is None or not await delete_person(session, user.id, person.id):
        await callback.answer(t(user.language, "debt.person.gone"))
        return
    text = t(user.language, "debt.delete.done", person=esc(person.name))
    await safe_edit(callback, text, back_to_list_keyboard(user.language))
    await callback.answer()
