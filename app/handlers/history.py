"""/history: the last 10 records, each with a delete button."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.handlers.utils import safe_edit
from app.i18n import t
from app.keyboards.manage import HDelCb, history_keyboard
from app.services.debts import undo_debt_entry
from app.services.history import recent_records, render_history
from app.services.transactions import undo_transaction

router = Router(name="history")


async def build_history(
    session: AsyncSession, user: User
) -> tuple[str, InlineKeyboardMarkup | None]:
    items = await recent_records(session, user.id)
    text = render_history(user.language, user.timezone, items)
    return text, (history_keyboard(items) if items else None)


@router.message(Command("history"))
async def cmd_history(message: Message, session: AsyncSession, user: User) -> None:
    text, markup = await build_history(session, user)
    await message.answer(text, reply_markup=markup)


@router.callback_query(HDelCb.filter())
async def on_delete_record(
    callback: CallbackQuery, callback_data: HDelCb, session: AsyncSession, user: User
) -> None:
    if callback_data.kind == "t":
        deleted = await undo_transaction(session, user.id, callback_data.record_id)
    elif callback_data.kind == "d":
        deleted = await undo_debt_entry(session, user.id, callback_data.record_id)
    else:
        await callback.answer(t(user.language, "expired"))
        return

    # Show the refreshed list (totals and balances follow from the stored records).
    text, markup = await build_history(session, user)
    await safe_edit(callback, text, markup)
    key = "history.deleted" if deleted is not None else "undo.already"
    await callback.answer(t(user.language, key))
