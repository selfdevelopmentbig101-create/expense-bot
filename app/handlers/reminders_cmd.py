"""The buttons under an overdue reminder, and /remindtest for trying reminders by hand."""
import html

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dates import parse_user_date
from app.core.money import format_amount
from app.core.reminders import POSTPONE_DAYS
from app.db.models import User
from app.handlers.debt_views import today_local
from app.handlers.utils import safe_edit
from app.i18n import t
from app.keyboards.debt import debt_undo_keyboard
from app.keyboards.reminder import RemCb
from app.scheduler.jobs import deliver_debt_reminders, deliver_evening_reminders
from app.services.debts import close_debt, get_person
from app.services.reminders import snooze_debt

router = Router(name="reminders")


@router.callback_query(RemCb.filter())
async def on_reminder_button(
    callback: CallbackQuery, callback_data: RemCb, session: AsyncSession, user: User
) -> None:
    lang, currency = user.language, callback_data.currency
    person = await get_person(session, user.id, callback_data.person_id)
    if person is None:
        await callback.answer(t(lang, "debt.person.gone"))
        return

    if callback_data.action == "ok":  # Repaid: write off what is left (has an Undo button)
        entry = await close_debt(
            session, user.id, person.id, currency, note=t(lang, "debt.close.note")
        )
        if entry is None:
            await callback.answer(t(lang, "debt.nothing"))
            return
        text = t(
            lang,
            "debt.close.done",
            person=html.escape(person.name),
            amount=format_amount(entry.amount, entry.currency),
        )
        await safe_edit(callback, text, debt_undo_keyboard(entry.id, lang))
    elif callback_data.action == "snz":  # Postpone
        if not await snooze_debt(session, user.id, person.id, currency, today_local(user)):
            await callback.answer(t(lang, "debt.nothing"))
            return
        await safe_edit(callback, t(lang, "reminder.postponed", days=POSTPONE_DAYS))
    await callback.answer()


@router.message(Command("remindtest"))
async def cmd_remindtest(
    message: Message, command: CommandObject, session: AsyncSession, user: User
) -> None:
    """/remindtest [DD.MM.YYYY]: send YOUR reminders now, as if today were that date.

    Debt reminders ignore the "already reminded" bookkeeping and the on/off switch, and
    nothing is recorded, so the test can be repeated. The evening reminder is sent too.
    """
    lang = user.language
    pretend_today = None
    if command.args and command.args.strip():
        pretend_today = parse_user_date(command.args.strip())
        if pretend_today is None:
            await message.answer(t(lang, "reminder.test_bad_date"))
            return
    debts = await deliver_debt_reminders(
        message.bot,
        session,
        user_id=user.id,
        only_enabled=False,
        ignore_history=True,
        today_override=pretend_today,
        mark=False,
    )
    await deliver_evening_reminders(message.bot, session, user_id=user.id, force=True, mark=False)
    await message.answer(t(lang, "reminder.test_done", debts=debts))
