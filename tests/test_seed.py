from sqlalchemy import func, select

from app.db.models import Category
from app.db.seed import DEFAULT_CATEGORIES, seed_default_categories
from app.i18n import CATALOG, LANGUAGES


async def test_seed_creates_defaults(session):
    added = await seed_default_categories(session)
    await session.commit()
    assert added == len(DEFAULT_CATEGORIES) == 11

    rows = (await session.scalars(select(Category))).all()
    assert sum(r.type == "expense" for r in rows) == 8
    assert sum(r.type == "income" for r in rows) == 3
    assert all(r.user_id is None and not r.is_archived for r in rows)


async def test_seed_is_idempotent(session):
    await seed_default_categories(session)
    await session.commit()
    assert await seed_default_categories(session) == 0
    await session.commit()
    total = await session.scalar(select(func.count()).select_from(Category))
    assert total == 11


def test_every_default_category_is_translated():
    for item in DEFAULT_CATEGORIES:
        for lang in LANGUAGES:
            assert item.key in CATALOG[lang], f"{item.key} missing in {lang}"


def test_expense_buttons_fit_the_spec_order():
    expense = [c.name for c in DEFAULT_CATEGORIES if c.type == "expense"]
    assert expense == [
        "Food", "Transport", "Home", "Health",
        "Clothes", "Fun", "Phone/Internet", "Other",
    ]
