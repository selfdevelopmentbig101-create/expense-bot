"""/undo (newest record of ANY kind) and the Undo button of income/expense records."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.handlers.utils import safe_edit
from app.i18n import t
from app.keyboards.entry import UndoCb
from app.services.debt_formatting import describe_debt_entry
from app.services.formatting import describe_entry
from app.services.transactions import undo_transaction
from app.services.undo import undo_last

router = Router(name="undo")


@router.message(Command("undo"))
async def cmd_undo(message: Message, session: AsyncSession, user: User) -> None:
    lang = user.language
    record = await undo_last(session, user.id)
    if record is None:
        await message.answer(t(lang, "undo.nothing"))
        return
    if record.debt is not None:
        summary = describe_debt_entry(lang, record.debt)
    else:
        summary = describe_entry(lang, record.transaction)
    await message.answer(t(lang, "undo.done", summary=summary))


@router.callback_query(UndoCb.filter())
async def on_undo_button(
    callback: CallbackQuery, callback_data: UndoCb, session: AsyncSession, user: User
) -> None:
    view = await undo_transaction(session, user.id, callback_data.transaction_id)
    if view is None:
        # Already undone (double tap). Do not touch the message.
        await callback.answer(t(user.language, "undo.already"))
        return
    text = t(user.language, "undo.done", summary=describe_entry(user.language, view))
    await safe_edit(callback, text)
    await callback.answer()
