"""Persons and debt entries (database access)."""
from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.debts import (
    NEW_DEBT_KINDS,
    DebtKind,
    balances as sum_balances,
    closing_entry,
    open_balances,
)
from app.db.models import DebtEntry, Person

MAX_NAME_LENGTH = 100


def clean_name(name: str) -> str:
    """Trim and collapse inner whitespace, keep the user's capitalisation."""
    return " ".join(name.split())[:MAX_NAME_LENGTH]


def normalize_name(name: str) -> str:
    """Key for case-insensitive matching: "  AZIZ " and "aziz" are the same person."""
    return clean_name(name).casefold()


@dataclass(frozen=True, slots=True)
class DebtEntryView:
    id: int
    person_id: int
    person_name: str
    kind: str
    amount: int
    currency: str
    note: str | None
    due_date: date | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PersonBalance:
    person_id: int
    name: str
    balances: dict[str, int]  # only open (non-zero) balances, signed


_VIEW_COLUMNS = (
    DebtEntry.id,
    DebtEntry.person_id,
    Person.name,
    DebtEntry.kind,
    DebtEntry.amount,
    DebtEntry.currency,
    DebtEntry.note,
    DebtEntry.due_date,
    DebtEntry.created_at,
)


# ----------------------------------------------------------------- persons
async def get_person(session: AsyncSession, user_id: int, person_id: int) -> Person | None:
    return await session.scalar(
        select(Person).where(Person.id == person_id, Person.user_id == user_id)
    )


async def find_person_by_name(session: AsyncSession, user_id: int, name: str) -> Person | None:
    return await session.scalar(
        select(Person).where(
            Person.user_id == user_id, Person.name_normalized == normalize_name(name)
        )
    )


async def get_or_create_person(
    session: AsyncSession, user_id: int, name: str, now: datetime | None = None
) -> Person:
    existing = await find_person_by_name(session, user_id, name)
    if existing is not None:
        return existing
    person = Person(
        user_id=user_id,
        name=clean_name(name),
        name_normalized=normalize_name(name),
        created_at=now or datetime.now(timezone.utc),
    )
    session.add(person)
    await session.flush()
    return person


async def recent_persons(session: AsyncSession, user_id: int, limit: int = 6) -> list[Person]:
    """The people the user dealt with most recently (last debt entry, else creation)."""
    last = (
        select(DebtEntry.person_id, func.max(DebtEntry.created_at).label("last_at"))
        .where(DebtEntry.user_id == user_id)
        .group_by(DebtEntry.person_id)
        .subquery()
    )
    result = await session.scalars(
        select(Person)
        .outerjoin(last, last.c.person_id == Person.id)
        .where(Person.user_id == user_id)
        .order_by(func.coalesce(last.c.last_at, Person.created_at).desc(), Person.id.desc())
        .limit(limit)
    )
    return list(result.all())


async def delete_person(session: AsyncSession, user_id: int, person_id: int) -> bool:
    """Delete a person together with their whole debt history."""
    if await get_person(session, user_id, person_id) is None:
        return False
    await session.execute(
        delete(DebtEntry).where(DebtEntry.person_id == person_id, DebtEntry.user_id == user_id)
    )
    result = await session.execute(
        delete(Person).where(Person.id == person_id, Person.user_id == user_id)
    )
    return result.rowcount == 1


# ----------------------------------------------------------------- entries
async def add_debt_entry(
    session: AsyncSession,
    *,
    user_id: int,
    person_id: int,
    kind: str,
    amount: int,
    currency: str,
    note: str | None = None,
    due_date: date | None = None,
    idempotency_key: str | None = None,
    now: datetime | None = None,
) -> DebtEntry:
    entry = DebtEntry(
        user_id=user_id,
        person_id=person_id,
        kind=DebtKind(kind).value,
        amount=amount,
        currency=currency,
        note=note,
        due_date=due_date,
        idempotency_key=idempotency_key,
        created_at=now or datetime.now(timezone.utc),
    )
    session.add(entry)
    await session.flush()
    return entry


async def get_debt_entry_view(
    session: AsyncSession, user_id: int, entry_id: int
) -> DebtEntryView | None:
    row = (
        await session.execute(
            select(*_VIEW_COLUMNS)
            .join(Person, Person.id == DebtEntry.person_id)
            .where(DebtEntry.id == entry_id, DebtEntry.user_id == user_id)
        )
    ).first()
    return DebtEntryView(*row) if row else None


async def entries_for_person(
    session: AsyncSession, user_id: int, person_id: int, limit: int = 10
) -> list[DebtEntryView]:
    """The person's history, newest first."""
    rows = await session.execute(
        select(*_VIEW_COLUMNS)
        .join(Person, Person.id == DebtEntry.person_id)
        .where(DebtEntry.user_id == user_id, DebtEntry.person_id == person_id)
        .order_by(DebtEntry.created_at.desc(), DebtEntry.id.desc())
        .limit(limit)
    )
    return [DebtEntryView(*row) for row in rows.all()]


async def undo_debt_entry(
    session: AsyncSession, user_id: int, entry_id: int
) -> DebtEntryView | None:
    """Delete one entry. A person left without any entry is removed too."""
    view = await get_debt_entry_view(session, user_id, entry_id)
    if view is None:
        return None
    result = await session.execute(
        delete(DebtEntry).where(DebtEntry.id == entry_id, DebtEntry.user_id == user_id)
    )
    if result.rowcount != 1:
        return None
    remaining = await session.scalar(
        select(func.count()).select_from(DebtEntry).where(DebtEntry.person_id == view.person_id)
    )
    if not remaining:
        await session.execute(
            delete(Person).where(Person.id == view.person_id, Person.user_id == user_id)
        )
    return view


async def get_last_debt_stamp(session: AsyncSession, user_id: int) -> tuple[int, datetime] | None:
    row = (
        await session.execute(
            select(DebtEntry.id, DebtEntry.created_at)
            .where(DebtEntry.user_id == user_id)
            .order_by(DebtEntry.created_at.desc(), DebtEntry.id.desc())
            .limit(1)
        )
    ).first()
    return (row[0], row[1]) if row else None


# ---------------------------------------------------------------- balances
async def get_person_balances(
    session: AsyncSession, user_id: int, person_id: int
) -> dict[str, int]:
    """Signed balance per currency, zero balances included."""
    rows = await session.execute(
        select(DebtEntry.kind, DebtEntry.amount, DebtEntry.currency).where(
            DebtEntry.user_id == user_id, DebtEntry.person_id == person_id
        )
    )
    return sum_balances(tuple(row) for row in rows.all())


async def get_overview(session: AsyncSession, user_id: int) -> list[PersonBalance]:
    """Everybody with at least one open balance. Closed debts are hidden."""
    rows = await session.execute(
        select(Person.id, Person.name, DebtEntry.kind, DebtEntry.amount, DebtEntry.currency)
        .join(DebtEntry, DebtEntry.person_id == Person.id)
        .where(Person.user_id == user_id, DebtEntry.user_id == user_id)
    )
    grouped: dict[int, tuple[str, list[tuple[str, int, str]]]] = {}
    for person_id, name, kind, amount, currency in rows.all():
        grouped.setdefault(person_id, (name, []))[1].append((kind, amount, currency))

    overview = []
    for person_id, (name, entries) in grouped.items():
        open_ones = open_balances(sum_balances(entries))
        if open_ones:
            overview.append(PersonBalance(person_id, name, open_ones))
    return sorted(overview, key=lambda item: (item.name.casefold(), item.person_id))


# ---------------------------------------------------------------- due dates
async def effective_due_date(
    session: AsyncSession, user_id: int, person_id: int, currency: str
) -> date | None:
    """Due date of the latest borrowed/lent entry that has one (per person + currency)."""
    return await session.scalar(
        select(DebtEntry.due_date)
        .where(
            DebtEntry.user_id == user_id,
            DebtEntry.person_id == person_id,
            DebtEntry.currency == currency,
            DebtEntry.kind.in_([kind.value for kind in NEW_DEBT_KINDS]),
            DebtEntry.due_date.is_not(None),
        )
        .order_by(DebtEntry.created_at.desc(), DebtEntry.id.desc())
        .limit(1)
    )


async def set_due_date(
    session: AsyncSession, user_id: int, person_id: int, currency: str, new_date: date | None
) -> bool:
    """Change the due date of (person, currency). None removes the deadline."""
    scope = (
        DebtEntry.user_id == user_id,
        DebtEntry.person_id == person_id,
        DebtEntry.currency == currency,
        DebtEntry.kind.in_([kind.value for kind in NEW_DEBT_KINDS]),
    )
    if new_date is None:
        await session.execute(update(DebtEntry).where(*scope).values(
                due_date=None, last_reminded_on=None, reminder_snoozed_until=None
            ))
        return True

    target = await session.scalar(
        select(DebtEntry.id)
        .where(*scope, DebtEntry.due_date.is_not(None))
        .order_by(DebtEntry.created_at.desc(), DebtEntry.id.desc())
        .limit(1)
    )
    if target is None:  # no entry has a deadline yet: use the newest borrowed/lent one
        target = await session.scalar(
            select(DebtEntry.id)
            .where(*scope)
            .order_by(DebtEntry.created_at.desc(), DebtEntry.id.desc())
            .limit(1)
        )
    if target is None:
        return False
    await session.execute(update(DebtEntry)
        .where(DebtEntry.id == target)
        .values(due_date=new_date, last_reminded_on=None, reminder_snoozed_until=None))
    return True


# ------------------------------------------------------------- close a debt
async def close_debt(
    session: AsyncSession,
    user_id: int,
    person_id: int,
    currency: str,
    note: str | None = None,
    now: datetime | None = None,
) -> DebtEntry | None:
    """Write off what is left: records the repayment that brings the balance to zero."""
    balance = (await get_person_balances(session, user_id, person_id)).get(currency, 0)
    closing = closing_entry(balance)
    if closing is None:
        return None
    kind, amount = closing
    return await add_debt_entry(
        session,
        user_id=user_id,
        person_id=person_id,
        kind=kind,
        amount=amount,
        currency=currency,
        note=note,
        now=now,
    )


async def recent_debt_entries(
    session: AsyncSession, user_id: int, limit: int = 10
) -> list[DebtEntryView]:
    """The newest debt entries of all people, newest first."""
    rows = await session.execute(
        select(*_VIEW_COLUMNS)
        .join(Person, Person.id == DebtEntry.person_id)
        .where(DebtEntry.user_id == user_id)
        .order_by(DebtEntry.created_at.desc(), DebtEntry.id.desc())
        .limit(limit)
    )
    return [DebtEntryView(*row) for row in rows.all()]


async def all_debt_entries(session: AsyncSession, user_id: int) -> list[DebtEntryView]:
    """Every debt entry of the user, oldest first (for the CSV export)."""
    rows = await session.execute(
        select(*_VIEW_COLUMNS)
        .join(Person, Person.id == DebtEntry.person_id)
        .where(DebtEntry.user_id == user_id)
        .order_by(DebtEntry.created_at, DebtEntry.id)
    )
    return [DebtEntryView(*row) for row in rows.all()]
