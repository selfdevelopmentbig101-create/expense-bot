"""Categories: reading them for the buttons and managing the user's own ones.

Built-in (default) categories are shared by everybody and cannot be changed.
A category that already has records is never deleted: it is hidden (archived),
so old records, reports and history keep working.
"""
from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.categories import (
    DEFAULT_CATEGORY_EMOJI,
    MAX_CATEGORY_NAME,
    MAX_CUSTOM_PER_TYPE,
    parse_category_input,
)
from app.db.models import Category, Transaction
from app.i18n import LANGUAGES, t


def category_name(lang: str, name_key: str | None, name: str) -> str:
    """Default categories are translated; custom ones keep the name the user typed."""
    return t(lang, name_key) if name_key else name


def category_label(lang: str, name_key: str | None, name: str, emoji: str) -> str:
    text = category_name(lang, name_key, name)
    return f"{emoji} {text}".strip()


def _visible_to(user_id: int):
    return or_(Category.user_id.is_(None), Category.user_id == user_id)


async def list_categories(session: AsyncSession, user_id: int, entry_type: str) -> list[Category]:
    """Default + the user's own categories of one type, without archived ones."""
    result = await session.scalars(
        select(Category)
        .where(
            Category.type == entry_type,
            Category.is_archived.is_(False),
            _visible_to(user_id),
        )
        .order_by(Category.sort_order, Category.id)
    )
    return list(result.all())


async def get_category_for_user(
    session: AsyncSession, user_id: int, category_id: int
) -> Category | None:
    """A usable category: shared or the user's own, and not archived."""
    return await session.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.is_archived.is_(False),
            _visible_to(user_id),
        )
    )


# ------------------------------------------------------------ own categories
async def get_own_category(
    session: AsyncSession, user_id: int, category_id: int
) -> Category | None:
    """Only the user's OWN, visible category. Built-in ones are never returned."""
    return await session.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.user_id == user_id,
            Category.is_archived.is_(False),
        )
    )


async def count_records(session: AsyncSession, category_id: int) -> int:
    return await session.scalar(
        select(func.count()).select_from(Transaction).where(Transaction.category_id == category_id)
    ) or 0


async def _count_own_active(session: AsyncSession, user_id: int, entry_type: str) -> int:
    return await session.scalar(
        select(func.count())
        .select_from(Category)
        .where(
            Category.user_id == user_id,
            Category.type == entry_type,
            Category.is_archived.is_(False),
        )
    ) or 0


async def _find_conflict(
    session: AsyncSession,
    user_id: int,
    entry_type: str,
    name: str,
    exclude_id: int | None = None,
) -> Category | None:
    """A category of the same type that already uses this name (any case).

    Built-in categories count with their names in ALL languages, so a user cannot add
    "\u0415\u0434\u0430" or "Oziq-ovqat" next to Food. Archived categories count too.
    """
    wanted = name.casefold()
    rows = await session.scalars(
        select(Category).where(Category.type == entry_type, _visible_to(user_id))
    )
    for category in rows.all():
        if category.id == exclude_id:
            continue
        names = {category.name.casefold()}
        if category.name_key:
            names |= {t(lang, category.name_key).casefold() for lang in LANGUAGES}
        if wanted in names:
            return category
    return None


class AddStatus(StrEnum):
    ADDED = "added"
    RESTORED = "restored"  # an archived category with that name came back
    EXISTS = "exists"
    INVALID = "invalid"
    LIMIT = "limit"


async def add_category(
    session: AsyncSession, user_id: int, entry_type: str, raw_text: str
) -> tuple[AddStatus, Category | None]:
    emoji, name = parse_category_input(raw_text)
    if not name or len(name) > MAX_CATEGORY_NAME:
        return AddStatus.INVALID, None

    active = await _count_own_active(session, user_id, entry_type)
    conflict = await _find_conflict(session, user_id, entry_type, name)
    if conflict is not None:
        if conflict.user_id == user_id and conflict.is_archived:
            if active >= MAX_CUSTOM_PER_TYPE:
                return AddStatus.LIMIT, None
            conflict.is_archived = False
            conflict.name = name
            if emoji:
                conflict.emoji = emoji
            await session.flush()
            return AddStatus.RESTORED, conflict
        return AddStatus.EXISTS, conflict

    if active >= MAX_CUSTOM_PER_TYPE:
        return AddStatus.LIMIT, None
    category = Category(
        user_id=user_id,
        name=name,
        emoji=emoji or DEFAULT_CATEGORY_EMOJI,
        type=entry_type,
        sort_order=100,  # after the built-in ones
    )
    session.add(category)
    await session.flush()
    return AddStatus.ADDED, category


class RenameStatus(StrEnum):
    RENAMED = "renamed"
    EXISTS = "exists"
    INVALID = "invalid"
    GONE = "gone"


async def rename_category(
    session: AsyncSession, user_id: int, category_id: int, raw_text: str
) -> tuple[RenameStatus, Category | None]:
    category = await get_own_category(session, user_id, category_id)
    if category is None:
        return RenameStatus.GONE, None
    emoji, name = parse_category_input(raw_text)
    if not name or len(name) > MAX_CATEGORY_NAME:
        return RenameStatus.INVALID, category
    if await _find_conflict(session, user_id, category.type, name, exclude_id=category.id):
        return RenameStatus.EXISTS, category
    category.name = name
    if emoji:
        category.emoji = emoji
    await session.flush()
    return RenameStatus.RENAMED, category


class RemoveStatus(StrEnum):
    DELETED = "deleted"  # it had no records
    HIDDEN = "hidden"  # it has records: archived, the records stay
    GONE = "gone"


@dataclass(frozen=True, slots=True)
class RemoveOutcome:
    status: RemoveStatus
    emoji: str = ""
    name: str = ""
    records: int = 0


async def remove_category(
    session: AsyncSession, user_id: int, category_id: int
) -> RemoveOutcome:
    """Delete an unused category, or hide one that already has records."""
    category = await get_own_category(session, user_id, category_id)
    if category is None:
        return RemoveOutcome(RemoveStatus.GONE)
    emoji, name = category.emoji, category.name
    records = await count_records(session, category.id)
    if records == 0:
        await session.execute(delete(Category).where(Category.id == category.id))
        return RemoveOutcome(RemoveStatus.DELETED, emoji, name, 0)
    category.is_archived = True
    await session.flush()
    return RemoveOutcome(RemoveStatus.HIDDEN, emoji, name, records)
