"""Finding out which reminders are due (no Telegram here, so it is easy to test)."""
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.debts import NEW_DEBT_KINDS, signed_amount
from app.core.reminders import POSTPONE_DAYS, ReminderKind, evening_due, reminder_kind
from app.db.models import DebtEntry, Person, User
from app.services.transactions import totals_between
from app.utils.timezone import get_zone, local_day_bounds

_NEW_KINDS = {kind.value for kind in NEW_DEBT_KINDS}


@dataclass(frozen=True, slots=True)
class DebtReminder:
    user_id: int
    telegram_id: int
    language: str
    person_id: int
    person_name: str
    currency: str
    balance: int  # signed: negative = I owe, positive = they owe me
    due: date
    kind: ReminderKind
    entry_id: int  # the entry that carries the due date and the reminder state
    today: date

    @property
    def amount(self) -> int:
        return abs(self.balance)


@dataclass(frozen=True, slots=True)
class EveningReminder:
    user_id: int
    telegram_id: int
    language: str
    local_date: date
    spent_today: dict[str, int]


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(timezone.utc)


async def collect_debt_reminders(
    session: AsyncSession,
    now: datetime | None = None,
    *,
    user_id: int | None = None,
    only_enabled: bool = True,
    ignore_history: bool = False,
    today_override: date | None = None,
) -> list[DebtReminder]:
    """Debts that need a reminder today. Per (person, currency): the balance must be open and
    the latest dated borrowed/lent entry decides the due date."""
    now = _now(now)
    query = select(User)
    if only_enabled:
        query = query.where(User.debt_reminders_enabled.is_(True))
    if user_id is not None:
        query = query.where(User.id == user_id)
    users = (await session.scalars(query.order_by(User.id))).all()

    reminders: list[DebtReminder] = []
    for user in users:
        today = today_override or now.astimezone(get_zone(user.timezone)).date()
        rows = await session.execute(
            select(
                DebtEntry.id, DebtEntry.person_id, Person.name, DebtEntry.kind, DebtEntry.amount,
                DebtEntry.currency, DebtEntry.due_date, DebtEntry.last_reminded_on,
                DebtEntry.reminder_snoozed_until,
            )
            .join(Person, Person.id == DebtEntry.person_id)
            .where(DebtEntry.user_id == user.id)
            .order_by(DebtEntry.created_at, DebtEntry.id)
        )
        groups: dict[tuple[int, str], dict] = {}
        for entry_id, person_id, name, kind, amount, currency, due, last, snooze in rows.all():
            group = groups.setdefault((person_id, currency), {"name": name, "balance": 0, "due": None})
            group["balance"] += signed_amount(kind, amount)
            if kind in _NEW_KINDS and due is not None:  # the newest dated one wins
                group["due"] = (entry_id, due, last, snooze)

        for (person_id, currency), group in groups.items():
            if group["balance"] == 0 or group["due"] is None:
                continue
            entry_id, due, last, snooze = group["due"]
            kind = reminder_kind(today, due, last, snooze, ignore_history=ignore_history)
            if kind is not None:
                reminders.append(
                    DebtReminder(
                        user.id, user.telegram_id, user.language, person_id, group["name"],
                        currency, group["balance"], due, kind, entry_id, today,
                    )
                )
    return sorted(reminders, key=lambda r: (r.user_id, r.person_name.casefold(), r.currency))


async def mark_reminded(session: AsyncSession, entry_id: int, on_date: date) -> None:
    await session.execute(
        update(DebtEntry).where(DebtEntry.id == entry_id).values(last_reminded_on=on_date)
    )


async def snooze_debt(
    session: AsyncSession,
    user_id: int,
    person_id: int,
    currency: str,
    today: date,
    days: int = POSTPONE_DAYS,
) -> bool:
    """Postpone: no reminders for `days` days. False when the debt has no due date."""
    entry_id = await session.scalar(
        select(DebtEntry.id)
        .where(
            DebtEntry.user_id == user_id,
            DebtEntry.person_id == person_id,
            DebtEntry.currency == currency,
            DebtEntry.kind.in_(_NEW_KINDS),
            DebtEntry.due_date.is_not(None),
        )
        .order_by(DebtEntry.created_at.desc(), DebtEntry.id.desc())
        .limit(1)
    )
    if entry_id is None:
        return False
    await session.execute(
        update(DebtEntry)
        .where(DebtEntry.id == entry_id)
        .values(reminder_snoozed_until=today + timedelta(days=days), last_reminded_on=today)
    )
    return True


async def collect_evening_reminders(
    session: AsyncSession,
    now: datetime | None = None,
    *,
    user_id: int | None = None,
    force: bool = False,
) -> list[EveningReminder]:
    """Users whose evening reminder time has come. force=True is for manual tests."""
    now = _now(now)
    query = select(User)
    if user_id is not None:
        query = query.where(User.id == user_id)
    if not (force and user_id is not None):
        query = query.where(User.reminder_time.is_not(None))
    result = []
    for user in (await session.scalars(query.order_by(User.id))).all():
        local_now = now.astimezone(get_zone(user.timezone))
        if not force and not evening_due(local_now, user.reminder_time, user.last_evening_reminded_on):
            continue
        start, end = local_day_bounds(now, user.timezone)
        spent = await totals_between(session, user.id, "expense", start, end)
        result.append(EveningReminder(user.id, user.telegram_id, user.language, local_now.date(), spent))
    return result


async def mark_evening_sent(session: AsyncSession, user_id: int, local_date: date) -> None:
    await session.execute(
        update(User).where(User.id == user_id).values(last_evening_reminded_on=local_date)
    )
