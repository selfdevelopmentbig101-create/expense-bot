from datetime import datetime, timezone

from sqlalchemy import func, select

from app.core.categories import MAX_CUSTOM_PER_TYPE
from app.db.models import Category
from app.db.seed import seed_default_categories
from app.services.categories import (
    AddStatus,
    RemoveStatus,
    RenameStatus,
    add_category,
    count_records,
    get_category_for_user,
    get_own_category,
    list_categories,
    remove_category,
    rename_category,
)
from app.services.transactions import save_transaction
from app.services.users import get_or_create_user

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)


async def setup(session, telegram_id=1):
    await seed_default_categories(session)
    user, _ = await get_or_create_user(session, telegram_id, None)
    return user


async def names(session, user, entry_type="expense"):
    return [c.name for c in await list_categories(session, user.id, entry_type)]


async def test_add_a_category_with_an_emoji(session):
    user = await setup(session)
    status, category = await add_category(session, user.id, "expense", "\U0001F436 Pets")
    assert status is AddStatus.ADDED
    assert (category.name, category.emoji, category.type, category.user_id) == ("Pets", "\U0001F436", "expense", user.id)
    assert (await names(session, user))[-1] == "Pets"  # after the built-in ones


async def test_add_without_an_emoji_uses_the_default_one(session):
    user = await setup(session)
    _, category = await add_category(session, user.id, "income", "Scholarship")
    assert category.emoji == "\U0001F3F7"
    assert "Scholarship" in await names(session, user, "income")


async def test_invalid_names_are_refused(session):
    user = await setup(session)
    for bad in ("", "   ", "\U0001F436", "x" * 31):
        assert (await add_category(session, user.id, "expense", bad))[0] is AddStatus.INVALID
    assert (await add_category(session, user.id, "expense", "x" * 30))[0] is AddStatus.ADDED


async def test_duplicates_are_refused_in_any_case(session):
    user = await setup(session)
    await add_category(session, user.id, "expense", "Pets")
    for text in ("pets", "  PETS ", "\U0001F408 Pets"):
        assert (await add_category(session, user.id, "expense", text))[0] is AddStatus.EXISTS


async def test_built_in_names_are_taken_in_all_languages(session):
    user = await setup(session)
    for text in ("food", "\u0415\u0434\u0430", "\u0435\u0434\u0430", "Oziq-ovqat", "phone/internet"):
        status, _ = await add_category(session, user.id, "expense", text)
        assert status is AddStatus.EXISTS, text


async def test_the_same_name_is_fine_for_the_other_type_and_other_users(session):
    user, other = await setup(session), None
    other, _ = await get_or_create_user(session, 2, None)
    assert (await add_category(session, user.id, "expense", "Gift"))[0] is AddStatus.ADDED  # Gift is income
    await add_category(session, user.id, "expense", "Pets")
    assert (await add_category(session, other.id, "expense", "Pets"))[0] is AddStatus.ADDED
    assert "Pets" not in [c.name for c in await list_categories(session, other.id, "income")]


async def test_the_number_of_own_categories_is_limited(session):
    user = await setup(session)
    for i in range(MAX_CUSTOM_PER_TYPE):
        assert (await add_category(session, user.id, "expense", f"Cat {i}"))[0] is AddStatus.ADDED
    assert (await add_category(session, user.id, "expense", "One more"))[0] is AddStatus.LIMIT
    assert (await add_category(session, user.id, "income", "Income one"))[0] is AddStatus.ADDED


async def test_rename(session):
    user = await setup(session)
    _, category = await add_category(session, user.id, "expense", "\U0001F436 Pets")
    status, renamed = await rename_category(session, user.id, category.id, "Animals")
    assert status is RenameStatus.RENAMED and (renamed.name, renamed.emoji) == ("Animals", "\U0001F436")
    status, renamed = await rename_category(session, user.id, category.id, "\U0001F408 Cats")
    assert (renamed.name, renamed.emoji) == ("Cats", "\U0001F408")
    status, _ = await rename_category(session, user.id, category.id, "cats")  # only the case changes
    assert status is RenameStatus.RENAMED


async def test_rename_rules(session):
    user, other = await setup(session), None
    other, _ = await get_or_create_user(session, 2, None)
    _, pets = await add_category(session, user.id, "expense", "Pets")
    await add_category(session, user.id, "expense", "Books")
    assert (await rename_category(session, user.id, pets.id, "books"))[0] is RenameStatus.EXISTS
    assert (await rename_category(session, user.id, pets.id, "Food"))[0] is RenameStatus.EXISTS
    assert (await rename_category(session, user.id, pets.id, "  "))[0] is RenameStatus.INVALID
    assert (await rename_category(session, other.id, pets.id, "Mine"))[0] is RenameStatus.GONE
    builtin = (await list_categories(session, user.id, "expense"))[0]
    assert (await rename_category(session, user.id, builtin.id, "Mine"))[0] is RenameStatus.GONE
    assert builtin.name == "Food"


async def test_an_unused_category_is_deleted(session):
    user = await setup(session)
    _, pets = await add_category(session, user.id, "expense", "Pets")
    outcome = await remove_category(session, user.id, pets.id)
    assert outcome.status is RemoveStatus.DELETED and outcome.name == "Pets"
    assert await session.scalar(select(func.count()).select_from(Category).where(Category.name == "Pets")) == 0
    assert (await remove_category(session, user.id, pets.id)).status is RemoveStatus.GONE


async def test_a_category_with_records_is_hidden_not_deleted(session):
    user = await setup(session)
    _, pets = await add_category(session, user.id, "expense", "Pets")
    await save_transaction(session, user_id=user.id, category_id=pets.id, entry_type="expense",
                           amount=7_000, currency="UZS", note=None, now=NOW)
    outcome = await remove_category(session, user.id, pets.id)
    assert (outcome.status, outcome.records) == (RemoveStatus.HIDDEN, 1)
    assert await count_records(session, pets.id) == 1  # the record is still there
    assert "Pets" not in await names(session, user)  # no button any more
    assert await get_category_for_user(session, user.id, pets.id) is None  # cannot be chosen
    assert await get_own_category(session, user.id, pets.id) is None


async def test_adding_the_same_name_brings_a_hidden_category_back(session):
    user = await setup(session)
    _, pets = await add_category(session, user.id, "expense", "Pets")
    await save_transaction(session, user_id=user.id, category_id=pets.id, entry_type="expense",
                           amount=1, currency="UZS", note=None, now=NOW)
    await remove_category(session, user.id, pets.id)
    status, back = await add_category(session, user.id, "expense", "\U0001F415 pets")
    assert status is AddStatus.RESTORED
    assert back.id == pets.id and back.emoji == "\U0001F415" and back.name == "pets"
    assert "pets" in await names(session, user)
    assert await count_records(session, back.id) == 1  # the old record is attached again


async def test_built_in_categories_and_other_peoples_categories_cannot_be_removed(session):
    user = await setup(session)
    other, _ = await get_or_create_user(session, 2, None)
    builtin = (await list_categories(session, user.id, "expense"))[0]
    assert (await remove_category(session, user.id, builtin.id)).status is RemoveStatus.GONE
    _, mine = await add_category(session, user.id, "expense", "Pets")
    assert (await remove_category(session, other.id, mine.id)).status is RemoveStatus.GONE
    assert "Pets" in await names(session, user)
