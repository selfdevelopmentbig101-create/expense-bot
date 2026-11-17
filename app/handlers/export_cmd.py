"""/export: two CSV files (income/expenses and debts) that open correctly in Excel."""
from datetime import datetime, timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.i18n import t
from app.services.export import export_debts_csv, export_transactions_csv
from app.utils.timezone import to_local

router = Router(name="export")


@router.message(Command("export"))
async def cmd_export(message: Message, session: AsyncSession, user: User) -> None:
    lang = user.language
    transactions = await export_transactions_csv(session, user)
    debts = await export_debts_csv(session, user)
    if transactions is None and debts is None:
        await message.answer(t(lang, "export.empty"))
        return

    stamp = to_local(datetime.now(timezone.utc), user.timezone).strftime("%Y-%m-%d")
    if transactions is not None:
        await message.answer_document(
            BufferedInputFile(transactions, filename=f"transactions_{stamp}.csv"),
            caption=t(lang, "export.caption.transactions"),
        )
    if debts is not None:
        await message.answer_document(
            BufferedInputFile(debts, filename=f"debts_{stamp}.csv"),
            caption=t(lang, "export.caption.debts"),
        )
