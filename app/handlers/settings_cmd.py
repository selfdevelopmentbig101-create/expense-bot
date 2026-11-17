"""/settings: currency, language, evening reminder time, debt reminders on/off."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.times import format_hhmm, parse_hhmm
from app.db.models import User
from app.handlers.debt_views import edit_or_send, message_ref
from app.handlers.utils import safe_edit
from app.i18n import LANGUAGE_NAMES, t
from app.keyboards.debt import cancel_keyboard
from app.keyboards.settings import (
    SetBackCb,
    SetCurrencyCb,
    SetDebtCb,
    SetEveningCb,
    SetOpenCb,
    currency_keyboard,
    evening_keyboard,
    language_choice_keyboard,
    settings_keyboard,
)
from app.services.pending import Pending, PendingState, consume_pending, create_pending
from app.services.settings import set_currency, set_reminder_time, toggle_debt_reminders

router = Router(name="settings")


def settings_screen(user: User) -> tuple[str, InlineKeyboardMarkup]:
    lang = user.language
    evening = format_hhmm(user.reminder_time) if user.reminder_time else t(lang, "settings.off")
    debts = t(lang, "settings.on" if user.debt_reminders_enabled else "settings.off")
    lines = [
        t(lang, "settings.title"),
        "",
        t(lang, "settings.language", value=LANGUAGE_NAMES[lang]),
        t(lang, "settings.currency", value=user.currency),
        t(lang, "settings.evening", value=evening),
        t(lang, "settings.debt", value=debts),
    ]
    return "\n".join(lines), settings_keyboard(lang, user.debt_reminders_enabled)


@router.message(Command("settings"))
async def cmd_settings(message: Message, user: User) -> None:
    text, markup = settings_screen(user)
    await message.answer(text, reply_markup=markup)


async def _show_settings(callback: CallbackQuery, user: User, toast: bool = False) -> None:
    text, markup = settings_screen(user)
    await safe_edit(callback, text, markup)
    await callback.answer(t(user.language, "settings.saved") if toast else None)


@router.callback_query(SetBackCb.filter())
async def on_back(callback: CallbackQuery, user: User) -> None:
    await _show_settings(callback, user)


@router.callback_query(SetOpenCb.filter())
async def on_open(callback: CallbackQuery, callback_data: SetOpenCb, user: User) -> None:
    lang = user.language
    if callback_data.section == "language":
        await safe_edit(callback, t(lang, "lang.choose"), language_choice_keyboard(lang))
    elif callback_data.section == "currency":
        await safe_edit(callback, t(lang, "settings.currency_prompt"), currency_keyboard(lang))
    elif callback_data.section == "evening":
        await safe_edit(callback, t(lang, "settings.evening_prompt"), evening_keyboard(lang))
    await callback.answer()


@router.callback_query(SetCurrencyCb.filter())
async def on_currency(callback: CallbackQuery, callback_data: SetCurrencyCb, user: User) -> None:
    set_currency(user, callback_data.code)
    await _show_settings(callback, user, toast=True)


@router.callback_query(SetEveningCb.filter())
async def on_evening(
    callback: CallbackQuery, callback_data: SetEveningCb, session: AsyncSession, user: User
) -> None:
    value = callback_data.value
    if value == "other":
        pending = await create_pending(
            session, user.id, PendingState.SETTINGS_TIME, dict(message_ref(callback))
        )
        await safe_edit(
            callback, t(user.language, "settings.ask_time"), cancel_keyboard(pending.token, user.language)
        )
        await callback.answer()
        return
    if value == "off":
        set_reminder_time(user, None)
    else:
        chosen = parse_hhmm(f"{value[:2]}:{value[2:]}")
        if chosen is None:
            await callback.answer(t(user.language, "expired"))
            return
        set_reminder_time(user, chosen)
    await _show_settings(callback, user, toast=True)


@router.callback_query(SetDebtCb.filter())
async def on_debt_toggle(callback: CallbackQuery, user: User) -> None:
    toggle_debt_reminders(user)
    await _show_settings(callback, user, toast=True)


# -------------------------------------------------------------- typed text
async def handle_settings_text(
    message: Message, session: AsyncSession, user: User, pending: Pending
) -> None:
    """The user typed a custom reminder time."""
    chosen = parse_hhmm(message.text or "")
    if chosen is None:
        await message.answer(t(user.language, "settings.time_invalid"))
        return
    await consume_pending(session, user.id, pending.token)
    set_reminder_time(user, chosen)
    text, markup = settings_screen(user)
    await edit_or_send(message, pending.payload, text, markup)
