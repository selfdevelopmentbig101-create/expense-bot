"""/budget: monthly limits per expense category."""
import html
from datetime import datetime, timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.money import format_amount
from app.core.parser import parse_amount
from app.db.models import User
from app.handlers.debt_views import edit_or_send, message_ref
from app.handlers.utils import AMOUNT_ERROR_KEYS, safe_edit
from app.i18n import t
from app.keyboards.budget import (
    BudgetAddCb,
    BudgetCatCb,
    BudgetListCb,
    BudgetMenuCb,
    BudgetRemoveCb,
    budget_menu_keyboard,
    budgets_keyboard,
    category_pick_keyboard,
)
from app.keyboards.debt import cancel_keyboard
from app.services.budget_formatting import render_budgets
from app.services.budgets import budget_overview, remove_budget, set_budget
from app.services.categories import get_category_for_user, list_categories
from app.services.pending import Pending, PendingState, consume_pending, create_pending
from app.utils.timezone import local_month_bounds

router = Router(name="budget")
ESC = html.escape


async def overview_screen(session: AsyncSession, user: User) -> tuple[str, InlineKeyboardMarkup]:
    start, end = local_month_bounds(datetime.now(timezone.utc), user.timezone)
    items = await budget_overview(session, user.id, start, end)
    return render_budgets(user.language, user.timezone, start, end, items), budgets_keyboard(items, user.language)


@router.message(Command("budget"))
async def cmd_budget(message: Message, session: AsyncSession, user: User) -> None:
    text, markup = await overview_screen(session, user)
    await message.answer(text, reply_markup=markup)


async def _show_overview(callback: CallbackQuery, session: AsyncSession, user: User, prefix: str = "") -> None:
    text, markup = await overview_screen(session, user)
    await safe_edit(callback, prefix + text, markup)


@router.callback_query(BudgetListCb.filter())
async def on_back(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    await _show_overview(callback, session, user)
    await callback.answer()


@router.callback_query(BudgetAddCb.filter())
async def on_add(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    categories = await list_categories(session, user.id, "expense")
    await safe_edit(
        callback,
        t(user.language, "budget.pick_category"),
        category_pick_keyboard(categories, user.language),
    )
    await callback.answer()


@router.callback_query(BudgetCatCb.filter())
async def on_category_chosen(
    callback: CallbackQuery, callback_data: BudgetCatCb, session: AsyncSession, user: User
) -> None:
    """Used for a new limit and for "change limit": both ask for the amount."""
    lang = user.language
    category = await get_category_for_user(session, user.id, callback_data.category_id)
    if category is None or category.type != "expense":
        await callback.answer(t(lang, "category.gone"))
        await _show_overview(callback, session, user)
        return
    pending = await create_pending(
        session,
        user.id,
        PendingState.BUDGET_AMOUNT,
        {"category_id": category.id, "currency": user.currency, **message_ref(callback)},
    )
    text = t(
        lang, "budget.ask_amount", emoji=category.emoji, name=ESC(category.name_key and t(lang, category.name_key) or category.name), currency=user.currency
    )
    await safe_edit(callback, text, cancel_keyboard(pending.token, lang))
    await callback.answer()


@router.callback_query(BudgetMenuCb.filter())
async def on_menu(
    callback: CallbackQuery, callback_data: BudgetMenuCb, session: AsyncSession, user: User
) -> None:
    lang = user.language
    start, end = local_month_bounds(datetime.now(timezone.utc), user.timezone)
    items = await budget_overview(session, user.id, start, end)
    item = next((i for i in items if i.category_id == callback_data.category_id), None)
    if item is None:
        await callback.answer(t(lang, "budget.gone"))
        await _show_overview(callback, session, user)
        return
    name = item.name_key and t(lang, item.name_key) or item.name
    text = t(
        lang,
        "budget.menu",
        emoji=item.emoji,
        name=ESC(name),
        limit=format_amount(item.limit, item.currency),
        spent=format_amount(item.spent, item.currency),
        percent=item.percent,
    )
    await safe_edit(callback, text, budget_menu_keyboard(item.category_id, lang))
    await callback.answer()


@router.callback_query(BudgetRemoveCb.filter())
async def on_remove(
    callback: CallbackQuery, callback_data: BudgetRemoveCb, session: AsyncSession, user: User
) -> None:
    lang = user.language
    category = await get_category_for_user(session, user.id, callback_data.category_id)
    removed = await remove_budget(session, user.id, callback_data.category_id)
    if not removed or category is None:
        await callback.answer(t(lang, "budget.gone"))
        await _show_overview(callback, session, user)
        return
    name = category.name_key and t(lang, category.name_key) or category.name
    prefix = t(lang, "budget.removed", emoji=category.emoji, name=ESC(name)) + "\n\n"
    await _show_overview(callback, session, user, prefix)
    await callback.answer()


# -------------------------------------------------------------- typed text
async def handle_budget_text(
    message: Message, session: AsyncSession, user: User, pending: Pending
) -> None:
    """The user typed the monthly limit."""
    lang, ref = user.language, pending.payload
    currency = ref["currency"]
    result = parse_amount(message.text or "", default_currency=currency)
    if result.error is not None:
        await message.answer(t(lang, AMOUNT_ERROR_KEYS.get(result.error, "amount.help")))
        return
    if result.currency != currency:
        await message.answer(t(lang, "budget.wrong_currency", currency=currency))
        return

    budget = await set_budget(session, user.id, ref["category_id"], result.amount, currency)
    await consume_pending(session, user.id, pending.token)
    category = await get_category_for_user(session, user.id, ref["category_id"])
    if budget is None or category is None:
        prefix = t(lang, "budget.gone") + "\n\n"
    else:
        name = category.name_key and t(lang, category.name_key) or category.name
        prefix = (
            t(
                lang,
                "budget.saved",
                emoji=category.emoji,
                name=ESC(name),
                limit=format_amount(result.amount, currency),
            )
            + "\n\n"
        )
    text, markup = await overview_screen(session, user)
    await edit_or_send(message, ref, prefix + text, markup)
