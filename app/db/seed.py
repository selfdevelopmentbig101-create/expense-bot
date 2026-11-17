"""Default (shared) categories. Seeding is idempotent."""
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Category, CategoryType


@dataclass(frozen=True)
class DefaultCategory:
    key: str  # i18n key and unique id
    name: str  # English fallback stored in the DB
    emoji: str
    type: CategoryType


DEFAULT_CATEGORIES: tuple[DefaultCategory, ...] = (
    DefaultCategory("cat.food", "Food", "🍞", CategoryType.EXPENSE),
    DefaultCategory("cat.transport", "Transport", "🚕", CategoryType.EXPENSE),
    DefaultCategory("cat.home", "Home", "🏠", CategoryType.EXPENSE),
    DefaultCategory("cat.health", "Health", "💊", CategoryType.EXPENSE),
    DefaultCategory("cat.clothes", "Clothes", "👕", CategoryType.EXPENSE),
    DefaultCategory("cat.fun", "Fun", "🎉", CategoryType.EXPENSE),
    DefaultCategory("cat.phone_internet", "Phone/Internet", "📱", CategoryType.EXPENSE),
    DefaultCategory("cat.other", "Other", "📦", CategoryType.EXPENSE),
    DefaultCategory("cat.salary", "Salary", "💼", CategoryType.INCOME),
    DefaultCategory("cat.gift", "Gift", "🎁", CategoryType.INCOME),
    DefaultCategory("cat.other_income", "Other income", "💰", CategoryType.INCOME),
)


async def seed_default_categories(session: AsyncSession) -> int:
    """Insert missing default categories. Returns how many were added.

    The caller is responsible for committing.
    """
    existing = set(
        (
            await session.scalars(
                select(Category.name_key).where(
                    Category.user_id.is_(None), Category.name_key.is_not(None)
                )
            )
        ).all()
    )
    added = 0
    for order, item in enumerate(DEFAULT_CATEGORIES):
        if item.key in existing:
            continue
        session.add(
            Category(
                user_id=None,
                name_key=item.key,
                name=item.name,
                emoji=item.emoji,
                type=item.type.value,
                sort_order=order,
            )
        )
        added += 1
    await session.flush()
    return added
