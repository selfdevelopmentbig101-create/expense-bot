"""/start, /language and the language picker callbacks."""
from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from app.db.models import User
from app.i18n import LANGUAGE_NAMES, LANGUAGES, t
from app.handlers.settings_cmd import settings_screen
from app.keyboards.language import LangCb, language_keyboard

router = Router(name="start")


def _greeting(lang: str) -> str:
    return f"{t(lang, 'start.guide')}\n\n{t(lang, 'lang.hint')}"


@router.message(CommandStart())
async def cmd_start(message: Message, user: User, is_new_user: bool) -> None:
    if is_new_user:
        # First contact: show the guide in the detected language + a picker.
        await message.answer(_greeting(user.language), reply_markup=language_keyboard("start"))
    else:
        await message.answer(t(user.language, "start.guide"))


@router.message(Command("language"))
async def cmd_language(message: Message, user: User) -> None:
    await message.answer(t(user.language, "lang.choose"), reply_markup=language_keyboard("cmd"))


@router.callback_query(LangCb.filter())
async def on_language(callback: CallbackQuery, callback_data: LangCb, user: User) -> None:
    if callback_data.code not in LANGUAGES:
        await callback.answer()
        return

    user.language = callback_data.code
    lang = user.language

    if callback_data.source == "start":
        text, markup = _greeting(lang), language_keyboard("start")
    elif callback_data.source == "settings":
        text, markup = settings_screen(user)
    else:
        text, markup = t(lang, "lang.changed", name=LANGUAGE_NAMES[lang]), None

    if isinstance(callback.message, Message):
        try:
            await callback.message.edit_text(text, reply_markup=markup)
        except TelegramBadRequest as exc:
            # Tapping the already selected language changes nothing.
            if "message is not modified" not in str(exc):
                raise
    await callback.answer()
