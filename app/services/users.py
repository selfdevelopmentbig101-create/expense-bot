"""User lookup and auto-creation."""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.i18n import detect_language


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    return await session.scalar(select(User).where(User.telegram_id == telegram_id))


async def get_or_create_user(
    session: AsyncSession, telegram_id: int, language_code: str | None
) -> tuple[User, bool]:
    """Return (user, created). The language is guessed from Telegram on creation."""
    user = await get_user_by_telegram_id(session, telegram_id)
    if user is not None:
        return user, False

    user = User(telegram_id=telegram_id, language=detect_language(language_code))
    session.add(user)
    try:
        await session.flush()
    except IntegrityError:
        # Two first messages arrived at the same time: the other one won.
        await session.rollback()
        existing = await get_user_by_telegram_id(session, telegram_id)
        if existing is None:
            raise
        return existing, False
    return user, True
