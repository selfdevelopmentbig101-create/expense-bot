"""Two things happen at the same instant: exactly one of them wins.

Each task uses its OWN session on the same SQLite file, like two Telegram updates handled at once.
"""
import asyncio
from datetime import datetime, timezone

from sqlalchemy import func, select

from app.db.models import DebtEntry, Transaction
from app.db.seed import seed_default_categories
from app.db.session import create_session_factory
from app.services.categories import list_categories
from app.services.debt_flow import DebtStatus, finalize_debt
from app.services.entry_flow import save_chosen_category
from app.services.pending import PendingState, create_pending
from app.services.transactions import save_transaction, undo_transaction
from app.services.users import get_or_create_user

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)


async def prepare(engine):
    factory = create_session_factory(engine)
    async with factory() as session:
        await seed_default_categories(session)
        user, _ = await get_or_create_user(session, 1, None)
        food = (await list_categories(session, user.id, "expense"))[0]
        await session.commit()
        return factory, user.id, food.id


async def count(factory, model):
    async with factory() as session:
        return await session.scalar(select(func.count()).select_from(model))


async def test_two_taps_on_the_same_category_save_one_record(engine):
    factory, user_id, food_id = await prepare(engine)
    async with factory() as session:
        user, _ = await get_or_create_user(session, 1, None)
        payload = {"amount": 10_000, "currency": "UZS", "type": "expense", "note": None}
        pending = await create_pending(session, user.id, PendingState.CHOOSE_CATEGORY, payload, NOW)
        await session.commit()

    async def tap():
        async with factory() as session:
            user, _ = await get_or_create_user(session, 1, None)
            saved = await save_chosen_category(session, user, pending.token, food_id, NOW)
            await session.commit()
            return saved

    results = await asyncio.gather(tap(), tap(), tap())
    assert sum(r is not None for r in results) == 1
    assert await count(factory, Transaction) == 1


async def test_two_taps_on_the_same_debt_button_save_one_entry(engine):
    factory, user_id, _ = await prepare(engine)
    async with factory() as session:
        user, _ = await get_or_create_user(session, 1, None)
        payload = {"flow": "debt", "amount": 500_000, "currency": "UZS", "type": "expense", "note": None,
                   "kind": "borrowed", "person_name": "Aziz"}
        pending = await create_pending(session, user.id, PendingState.DEBT_DUE, payload, NOW)
        await session.commit()

    async def tap():
        async with factory() as session:
            user, _ = await get_or_create_user(session, 1, None)
            outcome = await finalize_debt(session, user, pending.token, now=NOW)
            await session.commit()
            return outcome.status

    statuses = await asyncio.gather(tap(), tap())
    assert sorted(statuses) == sorted([DebtStatus.SAVED, DebtStatus.STALE])
    assert await count(factory, DebtEntry) == 1


async def test_two_undo_taps_delete_once(engine):
    factory, user_id, food_id = await prepare(engine)
    async with factory() as session:
        tx = await save_transaction(session, user_id=user_id, category_id=food_id, entry_type="expense",
                                    amount=1, currency="UZS", note=None, now=NOW)
        await session.commit()
        tx_id = tx.id

    async def tap():
        async with factory() as session:
            view = await undo_transaction(session, user_id, tx_id)
            await session.commit()
            return view

    results = await asyncio.gather(tap(), tap())
    assert sum(r is not None for r in results) == 1
    assert await count(factory, Transaction) == 0


async def test_two_first_messages_create_one_user(engine):
    factory = create_session_factory(engine)

    async def first_contact():
        async with factory() as session:
            user, created = await get_or_create_user(session, 777, "ru")
            await session.commit()
            return user.id, created

    (id_a, created_a), (id_b, created_b) = await asyncio.gather(first_contact(), first_contact())
    assert id_a == id_b
    assert sorted([created_a, created_b]) == [False, True]
