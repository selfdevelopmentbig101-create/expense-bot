"""The debt flow that starts from the "Debt" button under an expense amount.

Steps (one message, edited every time): kind -> person -> due date -> saved.
The same pending action moves through the states; every move is a conditional
UPDATE, so a double tap cannot advance twice. Typed text (a new person's name, a
due date, a repayment amount) is routed here by handle_pending_text().
"""
from aiogram import Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dates import due_from_choice, format_user_date, parse_user_date
from app.core.debts import NEW_DEBT_KINDS, DebtKind
from app.core.parser import ParseError, parse_amount
from app.db.models import User
from app.handlers.debt_views import (
    edit_or_send,
    message_ref,
    person_screen,
    present_outcome,
    render_state,
    today_local,
)
from app.handlers.utils import AMOUNT_ERROR_KEYS, safe_edit
from app.i18n import t
from app.keyboards.debt import DConfirmCb, DDueCb, DFullCb, DKindCb, DNewPersonCb, DPersonCb, DUndoCb
from app.keyboards.entry import DebtStartCb
from app.services.debt_flow import DebtStatus, finalize_debt
from app.services.debt_formatting import describe_debt_entry
from app.services.debts import (
    MAX_NAME_LENGTH,
    find_person_by_name,
    get_person,
    set_due_date,
    undo_debt_entry,
)
from app.services.formatting import NOTE_MAX
from app.services.pending import (
    Pending,
    PendingState,
    advance_pending,
    consume_pending,
    get_pending,
)

router = Router(name="debt_flow")


async def _move(
    session: AsyncSession,
    user: User,
    token: str,
    expected: set[PendingState],
    new_state: PendingState,
    updates: dict | None = None,
) -> Pending | None:
    """Advance the pending action one step. None if it is stale or already moved."""
    pending = await get_pending(session, user.id, token)
    if pending is None or pending.state not in expected:
        return None
    payload = {**pending.payload, **(updates or {})}
    return await advance_pending(
        session, user.id, token, expected=pending.state, new_state=new_state, payload=payload
    )


async def _stale(callback: CallbackQuery, user: User) -> None:
    await callback.answer(t(user.language, "expired"))


async def _show_state(
    callback: CallbackQuery, session: AsyncSession, user: User, pending: Pending
) -> None:
    text, markup = await render_state(session, user, pending)
    await safe_edit(callback, text, markup)
    await callback.answer()


async def _finish_callback(
    callback: CallbackQuery, session: AsyncSession, user: User, token: str, **kwargs
) -> None:
    outcome = await finalize_debt(session, user, token, **kwargs)
    shown = present_outcome(user.language, token, outcome)
    if shown is None:
        key = "debt.person.gone" if outcome.status is DebtStatus.BAD else "expired"
        await callback.answer(t(user.language, key))
        return
    await safe_edit(callback, *shown)
    await callback.answer()


# ------------------------------------------------------------------ buttons
@router.callback_query(DebtStartCb.filter())
async def on_debt_start(
    callback: CallbackQuery, callback_data: DebtStartCb, session: AsyncSession, user: User
) -> None:
    pending = await get_pending(session, user.id, callback_data.token)
    if (
        pending is None
        or pending.state is not PendingState.CHOOSE_CATEGORY
        or pending.payload.get("type") != "expense"  # income can never be a debt
    ):
        await _stale(callback, user)
        return
    moved = await _move(
        session, user, callback_data.token, {PendingState.CHOOSE_CATEGORY}, PendingState.DEBT_KIND
    )
    if moved is None:
        await _stale(callback, user)
        return
    await _show_state(callback, session, user, moved)


@router.callback_query(DKindCb.filter())
async def on_kind(
    callback: CallbackQuery, callback_data: DKindCb, session: AsyncSession, user: User
) -> None:
    try:
        kind = DebtKind(callback_data.kind)
    except ValueError:
        await _stale(callback, user)
        return
    moved = await _move(
        session,
        user,
        callback_data.token,
        {PendingState.DEBT_KIND},
        PendingState.DEBT_PERSON,
        {"kind": kind.value},
    )
    if moved is None:
        await _stale(callback, user)
        return
    await _show_state(callback, session, user, moved)


@router.callback_query(DPersonCb.filter())
async def on_person(
    callback: CallbackQuery, callback_data: DPersonCb, session: AsyncSession, user: User
) -> None:
    person = await get_person(session, user.id, callback_data.person_id)
    if person is None:
        await callback.answer(t(user.language, "debt.person.gone"))
        return
    updates = {"person_id": person.id, "person_name": person.name}
    pending = await get_pending(session, user.id, callback_data.token)
    if pending is None or pending.state is not PendingState.DEBT_PERSON:
        await _stale(callback, user)
        return

    if DebtKind(pending.payload["kind"]) in NEW_DEBT_KINDS:
        moved = await _move(
            session, user, callback_data.token, {PendingState.DEBT_PERSON}, PendingState.DEBT_DUE, updates
        )
        if moved is None:
            await _stale(callback, user)
            return
        await _show_state(callback, session, user, moved)
    else:  # a repayment has no due date: check it and save
        await _finish_callback(callback, session, user, callback_data.token, overrides=updates)


@router.callback_query(DNewPersonCb.filter())
async def on_new_person(
    callback: CallbackQuery, callback_data: DNewPersonCb, session: AsyncSession, user: User
) -> None:
    moved = await _move(
        session,
        user,
        callback_data.token,
        {PendingState.DEBT_PERSON},
        PendingState.DEBT_NEW_NAME,
        message_ref(callback),
    )
    if moved is None:
        await _stale(callback, user)
        return
    await _show_state(callback, session, user, moved)


async def _apply_due_change(
    session: AsyncSession, user: User, payload: dict, due
) -> tuple[str, object] | None:
    """/debts > Change due date: store it and return the refreshed person screen."""
    await set_due_date(session, user.id, payload["person_id"], payload["currency"], due)
    return await person_screen(session, user, payload["person_id"])


@router.callback_query(DDueCb.filter())
async def on_due(
    callback: CallbackQuery, callback_data: DDueCb, session: AsyncSession, user: User
) -> None:
    pending = await get_pending(session, user.id, callback_data.token)
    if pending is None or pending.state is not PendingState.DEBT_DUE:
        await _stale(callback, user)
        return

    if callback_data.choice == "pick":
        moved = await _move(
            session,
            user,
            callback_data.token,
            {PendingState.DEBT_DUE},
            PendingState.DEBT_DUE_TEXT,
            message_ref(callback),
        )
        if moved is None:
            await _stale(callback, user)
            return
        await _show_state(callback, session, user, moved)
        return

    try:
        due = due_from_choice(callback_data.choice, today_local(user))
    except ValueError:
        await _stale(callback, user)
        return

    if pending.payload.get("mode") == "change_due":
        if await consume_pending(session, user.id, callback_data.token) is None:
            await _stale(callback, user)
            return
        screen = await _apply_due_change(session, user, pending.payload, due)
        if screen is None:
            await callback.answer(t(user.language, "debt.person.gone"))
            return
        await safe_edit(callback, *screen)
        await callback.answer()
        return

    await _finish_callback(
        callback,
        session,
        user,
        callback_data.token,
        overrides={"due": due.isoformat() if due else None},
    )


@router.callback_query(DConfirmCb.filter())
async def on_confirm(
    callback: CallbackQuery, callback_data: DConfirmCb, session: AsyncSession, user: User
) -> None:
    if callback_data.mode == "debt":
        await _finish_callback(callback, session, user, callback_data.token, as_debt=True)
    elif callback_data.mode == "force":
        await _finish_callback(callback, session, user, callback_data.token, force=True)
    else:
        await _stale(callback, user)


@router.callback_query(DFullCb.filter())
async def on_full_amount(
    callback: CallbackQuery, callback_data: DFullCb, session: AsyncSession, user: User
) -> None:
    pending = await get_pending(session, user.id, callback_data.token)
    if pending is None or pending.state is not PendingState.DEBT_REPAY_AMOUNT:
        await _stale(callback, user)
        return
    await _finish_callback(
        callback,
        session,
        user,
        callback_data.token,
        overrides={"amount": pending.payload["owed"]},
    )


@router.callback_query(DUndoCb.filter())
async def on_debt_undo(
    callback: CallbackQuery, callback_data: DUndoCb, session: AsyncSession, user: User
) -> None:
    view = await undo_debt_entry(session, user.id, callback_data.entry_id)
    if view is None:
        await callback.answer(t(user.language, "undo.already"))  # double tap: leave the message alone
        return
    summary = describe_debt_entry(user.language, view)
    await safe_edit(callback, t(user.language, "undo.done", summary=summary))
    await callback.answer()


# -------------------------------------------------------------- typed text
async def handle_pending_text(
    message: Message, session: AsyncSession, user: User, pending: Pending
) -> None:
    """The user typed something while the bot waits for a name, a date or an amount."""
    lang = user.language
    text = (message.text or "").strip()
    p, token = pending.payload, pending.token

    async def finish(**kwargs) -> None:
        outcome = await finalize_debt(session, user, token, **kwargs)
        shown = present_outcome(lang, token, outcome)
        if shown is None:
            key = "debt.person.gone" if outcome.status is DebtStatus.BAD else "expired"
            await message.answer(t(lang, key))
            return
        await edit_or_send(message, p, *shown)

    if pending.state is PendingState.DEBT_NEW_NAME:
        name = " ".join(text.split())
        if not name or len(name) > MAX_NAME_LENGTH:
            await message.answer(t(lang, "debt.person.name_invalid"))
            return
        existing = await find_person_by_name(session, user.id, name)  # case-insensitive
        updates = {
            "person_id": existing.id if existing else None,
            "person_name": existing.name if existing else name,
        }
        if DebtKind(p["kind"]) in NEW_DEBT_KINDS:
            moved = await _move(
                session, user, token, {PendingState.DEBT_NEW_NAME}, PendingState.DEBT_DUE, updates
            )
            if moved is None:
                await message.answer(t(lang, "expired"))
                return
            screen = await render_state(session, user, moved)
            await edit_or_send(message, p, *screen)
        else:
            await finish(overrides=updates)
        return

    if pending.state is PendingState.DEBT_DUE_TEXT:
        due = parse_user_date(text)
        if due is None:
            example = format_user_date(today_local(user))
            await message.answer(t(lang, "debt.due.invalid", example=example))
            return
        if due < today_local(user):
            await message.answer(t(lang, "debt.due.past"))
            return
        if p.get("mode") == "change_due":
            if await consume_pending(session, user.id, token) is None:
                await message.answer(t(lang, "expired"))
                return
            screen = await _apply_due_change(session, user, p, due)
            if screen is None:
                await message.answer(t(lang, "debt.person.gone"))
                return
            await edit_or_send(message, p, *screen)
        else:
            await finish(overrides={"due": due.isoformat()})
        return

    if pending.state is PendingState.DEBT_REPAY_AMOUNT:
        result = parse_amount(text, default_currency=p["currency"])
        if result.error is not None:
            key = AMOUNT_ERROR_KEYS.get(result.error, "amount.help")
            await message.answer(t(lang, key))
            return
        if result.currency != p["currency"]:
            await message.answer(t(lang, "debt.repay.wrong_currency", currency=p["currency"]))
            return
        note = result.note[:NOTE_MAX] if result.note else None
        await finish(overrides={"amount": result.amount, "note": note})
