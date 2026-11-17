"""The two-step flow: amount message -> category buttons -> saved record."""
import html

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.messages import MAX_TEXT_LENGTH, is_plain_text, message_text
from app.core.money import CURRENCY_EXPONENTS, DEFAULT_CURRENCY, format_amount
from app.core.parser import ParseError, ParseResult, is_large_amount, parse_amount
from app.db.models import User
from app.handlers.text_router import route_pending_text
from app.handlers.utils import AMOUNT_ERROR_KEYS, safe_edit
from app.i18n import t
from app.keyboards.entry import (
    CancelCb,
    CatCb,
    LargeOkCb,
    PickCb,
    amount_keyboard,
    category_keyboard,
    large_amount_keyboard,
    undo_keyboard,
)
from app.services.budget_formatting import render_budget_alert
from app.services.categories import category_name, list_categories
from app.services.entry_flow import save_chosen_category
from app.services.formatting import NOTE_MAX, note_suffix
from app.services.pending import (
    TEXT_STATES,
    PendingState,
    consume_pending,
    create_pending,
    get_current_pending,
    get_pending,
)

router = Router(name="expense_flow")

def _short(note: str | None) -> str | None:
    return note[:NOTE_MAX] if note else None


async def _present(
    session: AsyncSession, user: User, state: PendingState, payload: dict
) -> tuple[str, InlineKeyboardMarkup]:
    """Create the pending action (replacing any old one) and build its message."""
    lang = user.language
    pending = await create_pending(session, user.id, state, payload)

    if state is PendingState.CHOOSE_CATEGORY:
        categories = await list_categories(session, user.id, payload["type"])
        key = "pending.income" if payload["type"] == "income" else "pending.expense"
        text = t(
            lang,
            key,
            amount=format_amount(payload["amount"], payload["currency"]),
            note=note_suffix(payload["note"]),
        )
        return text, category_keyboard(
            pending.token, categories, lang, with_debt=payload["type"] == "expense"
        )

    if state is PendingState.CONFIRM_LARGE:
        text = t(
            lang, "large.confirm", amount=format_amount(payload["amount"], payload["currency"])
        )
        return text, large_amount_keyboard(pending.token, lang)

    return t(lang, "multi.ask"), amount_keyboard(pending.token, payload["candidates"], lang)


def _next_state(amount: int, currency: str) -> PendingState:
    if is_large_amount(amount, currency):
        return PendingState.CONFIRM_LARGE
    return PendingState.CHOOSE_CATEGORY


@router.message(F.func(is_plain_text))
async def on_text(message: Message, session: AsyncSession, user: User) -> None:
    text = message_text(message) or ""  # a photo with a caption works like a text message
    if len(text) > MAX_TEXT_LENGTH:
        await message.answer(t(user.language, "msg.too_long"))
        return

    # While the bot waits for a name, a date or a repayment amount, the text is that answer.
    current = await get_current_pending(session, user.id)
    if current is not None and current.state in TEXT_STATES:
        if message.text is None:  # a photo caption cannot answer a question
            await message.answer(t(user.language, "msg.only_text"))
            return
        await route_pending_text(message, session, user, current)
        return

    lang = user.language
    default_currency = user.currency if user.currency in CURRENCY_EXPONENTS else DEFAULT_CURRENCY
    result: ParseResult = parse_amount(text, default_currency=default_currency)

    if result.error is ParseError.MULTIPLE_AMOUNTS:
        payload = {
            "type": result.type.value,
            "candidates": [
                {"amount": c.amount, "currency": c.currency, "note": _short(c.note)}
                for c in result.candidates
            ],
        }
        text, markup = await _present(session, user, PendingState.CHOOSE_AMOUNT, payload)
    elif result.error is not None:
        await message.answer(t(lang, AMOUNT_ERROR_KEYS[result.error]))
        return
    else:
        payload = {
            "amount": result.amount,
            "currency": result.currency,
            "type": result.type.value,
            "note": _short(result.note),
        }
        text, markup = await _present(
            session, user, _next_state(result.amount, result.currency), payload
        )
    await message.answer(text, reply_markup=markup)


async def _stale(callback: CallbackQuery, user: User) -> None:
    """Expired, replaced or already used. Only a toast: never touch the message,
    because after a double tap it already shows the saved record."""
    await callback.answer(t(user.language, "expired"))


@router.callback_query(CatCb.filter())
async def on_category(
    callback: CallbackQuery, callback_data: CatCb, session: AsyncSession, user: User
) -> None:
    saved = await save_chosen_category(session, user, callback_data.token, callback_data.category_id)
    if saved is None:
        await _stale(callback, user)
        return

    lang = user.language
    key = "saved.income" if saved.type == "income" else "saved.expense"
    text = t(
        lang,
        key,
        amount=format_amount(saved.amount, saved.currency),
        category=html.escape(category_name(lang, saved.category_name_key, saved.category_name)),
        note=note_suffix(saved.note),
        total=format_amount(saved.total_today, saved.currency),
    )
    if saved.budget is not None:  # this expense crossed 80% or 100% of the monthly limit
        text += "\n\n" + render_budget_alert(
            lang, saved.budget, saved.category_name_key, saved.category_name, saved.category_emoji
        )
    await safe_edit(callback, text, undo_keyboard(saved.transaction_id, lang))
    await callback.answer()


@router.callback_query(CancelCb.filter())
async def on_cancel(
    callback: CallbackQuery, callback_data: CancelCb, session: AsyncSession, user: User
) -> None:
    if await consume_pending(session, user.id, callback_data.token) is None:
        await _stale(callback, user)
        return
    await safe_edit(callback, t(user.language, "cancelled"))
    await callback.answer()


@router.callback_query(LargeOkCb.filter())
async def on_large_confirmed(
    callback: CallbackQuery, callback_data: LargeOkCb, session: AsyncSession, user: User
) -> None:
    pending = await get_pending(session, user.id, callback_data.token)
    if pending is None or pending.state is not PendingState.CONFIRM_LARGE:
        await _stale(callback, user)
        return
    if await consume_pending(session, user.id, callback_data.token) is None:
        await _stale(callback, user)
        return

    text, markup = await _present(session, user, PendingState.CHOOSE_CATEGORY, pending.payload)
    await safe_edit(callback, text, markup)
    await callback.answer()


@router.callback_query(PickCb.filter())
async def on_amount_picked(
    callback: CallbackQuery, callback_data: PickCb, session: AsyncSession, user: User
) -> None:
    pending = await get_pending(session, user.id, callback_data.token)
    if pending is None or pending.state is not PendingState.CHOOSE_AMOUNT:
        await _stale(callback, user)
        return
    candidates = pending.payload["candidates"]
    if not 0 <= callback_data.index < len(candidates):
        await _stale(callback, user)
        return
    if await consume_pending(session, user.id, callback_data.token) is None:
        await _stale(callback, user)
        return

    chosen = candidates[callback_data.index]
    payload = {
        "amount": chosen["amount"],
        "currency": chosen["currency"],
        "type": pending.payload["type"],
        "note": chosen["note"],
    }
    state = _next_state(chosen["amount"], chosen["currency"])
    text, markup = await _present(session, user, state, payload)
    await safe_edit(callback, text, markup)
    await callback.answer()
