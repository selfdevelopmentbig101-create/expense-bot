"""Screens shared by the debt flow and /debts: what to show for each step."""
from datetime import date, datetime, timezone

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dates import format_user_date
from app.core.debts import open_balances
from app.core.money import format_amount
from app.db.models import User
from app.i18n import t
from app.keyboards.debt import (
    cancel_keyboard,
    confirm_keyboard,
    debts_list_keyboard,
    due_keyboard,
    kind_keyboard,
    person_actions_keyboard,
    person_choice_keyboard,
    repay_keyboard,
)
from app.services.debt_flow import DebtOutcome, DebtStatus
from app.services.debt_formatting import esc, render_confirm, render_debt_saved, render_debts, render_person
from app.services.debts import (
    effective_due_date,
    entries_for_person,
    get_overview,
    get_person,
    get_person_balances,
    recent_persons,
)
from app.services.formatting import note_suffix
from app.services.pending import Pending, PendingState
from app.utils.timezone import to_local

from app.keyboards.debt import debt_undo_keyboard


def today_local(user: User, now: datetime | None = None) -> date:
    return to_local(now or datetime.now(timezone.utc), user.timezone).date()


def message_ref(callback: CallbackQuery) -> dict:
    """Where the flow message lives, so typed text can edit it later."""
    if isinstance(callback.message, Message):
        return {"chat_id": callback.message.chat.id, "message_id": callback.message.message_id}
    return {}


async def edit_or_send(
    message: Message, ref: dict, text: str, markup: InlineKeyboardMarkup | None
) -> None:
    """Edit the flow message; if that is impossible, send a new one."""
    if ref.get("chat_id") and ref.get("message_id"):
        try:
            await message.bot.edit_message_text(
                text, chat_id=ref["chat_id"], message_id=ref["message_id"], reply_markup=markup
            )
            return
        except TelegramBadRequest:
            pass
    await message.answer(text, reply_markup=markup)


async def render_state(
    session: AsyncSession, user: User, pending: Pending
) -> tuple[str, InlineKeyboardMarkup]:
    """The message and keyboard for the current step of a debt flow."""
    lang, p, token = user.language, pending.payload, pending.token
    currency = p.get("currency", "UZS")
    amount = format_amount(p["amount"], currency) if p.get("amount") else ""
    kind_text = t(lang, f"debt.kind.{p['kind']}") if p.get("kind") else ""
    person = esc(p.get("person_name") or "")

    state = pending.state
    if state is PendingState.DEBT_KIND:
        text = t(lang, "debt.kind.prompt", amount=amount, note=note_suffix(p.get("note")))
        return text, kind_keyboard(token, lang)

    if state is PendingState.DEBT_PERSON:
        persons = await recent_persons(session, user.id, limit=6)
        text = t(lang, "debt.person.prompt", kind=kind_text, amount=amount)
        return text, person_choice_keyboard(token, persons, lang)

    if state is PendingState.DEBT_NEW_NAME:
        return t(lang, "debt.person.ask_name"), cancel_keyboard(token, lang)

    if state is PendingState.DEBT_DUE:
        if p.get("mode") == "change_due":
            text = t(lang, "debt.due.change_prompt", person=person, currency=currency)
        else:
            text = t(lang, "debt.due.prompt", kind=kind_text, amount=amount, person=person)
        return text, due_keyboard(token, lang)

    if state is PendingState.DEBT_DUE_TEXT:
        example = format_user_date(today_local(user))
        return t(lang, "debt.due.ask_date", example=example), cancel_keyboard(token, lang)

    if state is PendingState.DEBT_REPAY_AMOUNT:
        owed = format_amount(p["owed"], currency)
        key = "debt.repay.prompt_by_me" if p["kind"] == "repaid_by_me" else "debt.repay.prompt_to_me"
        text = t(lang, key, person=person, owed=owed)
        return text, repay_keyboard(token, t(lang, "debt.repay.full", amount=owed), lang)

    raise ValueError(f"No screen for {state}")


def present_outcome(
    lang: str, token: str, outcome: DebtOutcome
) -> tuple[str, InlineKeyboardMarkup] | None:
    """Message for the result of finalize_debt, or None when there is nothing to show."""
    if outcome.status is DebtStatus.SAVED:
        return render_debt_saved(lang, outcome), debt_undo_keyboard(outcome.entry.id, lang)
    if outcome.status in (DebtStatus.CONFIRM_NO_DEBT, DebtStatus.CONFIRM_OVERPAY):
        mode = "debt" if outcome.status is DebtStatus.CONFIRM_NO_DEBT else "force"
        return render_confirm(lang, outcome), confirm_keyboard(token, mode, lang)
    return None


async def overview_screen(session: AsyncSession, user: User) -> tuple[str, InlineKeyboardMarkup | None]:
    overview = await get_overview(session, user.id)
    text = render_debts(user.language, overview)
    return text, (debts_list_keyboard(overview) if overview else None)


async def person_screen(
    session: AsyncSession, user: User, person_id: int
) -> tuple[str, InlineKeyboardMarkup] | None:
    """One person's balances, history and action buttons. None if the person is gone."""
    person = await get_person(session, user.id, person_id)
    if person is None:
        return None
    balances = await get_person_balances(session, user.id, person.id)
    still_open = open_balances(balances)
    dues = {c: await effective_due_date(session, user.id, person.id, c) for c in still_open}
    entries = await entries_for_person(session, user.id, person.id, limit=10)
    text = render_person(user.language, user.timezone, person.name, balances, dues, entries)
    return text, person_actions_keyboard(person.id, still_open, user.language)
