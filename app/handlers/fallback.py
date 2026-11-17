"""Last router: commands that do not exist, and messages that are not text."""
from aiogram import F, Router
from aiogram.types import Message

from app.db.models import User
from app.i18n import t

router = Router(name="fallback")


@router.message(F.text.startswith("/"))
async def unknown_command(message: Message, user: User) -> None:
    await message.answer(t(user.language, "cmd.soon"))


@router.message(~F.text, ~F.caption)
async def unsupported_content(message: Message, user: User) -> None:
    """Stickers, photos without a caption, voice messages, locations, polls ..."""
    await message.answer(t(user.language, "msg.only_text"))
