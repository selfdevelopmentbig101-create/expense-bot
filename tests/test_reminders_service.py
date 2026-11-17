from datetime import date, datetime, timedelta, timezone

from app.core.reminders import ReminderKind
from app.services.debts import add_debt_entry, get_or_create_person, set_due_date
from app.services.reminders import (
    collect_debt_reminders,
    collect_evening_reminders,
    mark_evening_sent,
    mark_reminded,
    snooze_debt,
)
from app.services.settings import set_reminder_time
from app.services.users import get_or_create_user
from app.db.seed import seed_default_categories
from app.services.categories import list_categories
from app.services.transactions import save_transaction
from datetime import time

DUE = date(2026, 11, 25)
CREATED = datetime(2026, 11, 10, 12, 0, tzinfo=timezone.utc)


def morning(day: date) -> datetime:
    """09:00 in Tashkent = 04:00 UTC: when the daily job runs."""
    return datetime(day.year, day.month, day.day, 4, 0, tzinfo=timezone.utc)


async def make_user(session, telegram_id=1):
    user, _ = await get_or_create_user(session, telegram_id, None)
    return user


async def debt(session, user, name="Aziz", kind="borrowed", amount=500_000, currency="UZS", due=DUE, hours=0):
    person = await get_or_create_person(session, user.id, name, CREATED)
    entry = await add_debt_entry(session, user_id=user.id, person_id=person.id, kind=kind, amount=amount,
                                 currency=currency, due_date=due, now=CREATED + timedelta(hours=hours))
    return person, entry


async def kinds(session, day, **kwargs):
    return [r.kind for r in await collect_debt_reminders(session, morning(day), **kwargs)]


async def test_one_day_before_on_the_day_and_when_overdue(session):
    user = await make_user(session)
    await debt(session, user)
    assert await kinds(session, date(2026, 11, 23)) == []
    assert await kinds(session, date(2026, 11, 24)) == [ReminderKind.TOMORROW]
    assert await kinds(session, date(2026, 11, 25)) == [ReminderKind.TODAY]
    assert await kinds(session, date(2026, 11, 26)) == [ReminderKind.OVERDUE]


async def test_both_directions(session):
    user = await make_user(session)
    await debt(session, user, "Aziz", "borrowed", 500_000)
    await debt(session, user, "Bobur", "lent", 200_000)
    found = await collect_debt_reminders(session, morning(date(2026, 11, 25)))
    by_name = {r.person_name: r for r in found}
    assert by_name["Aziz"].balance == -500_000 and by_name["Aziz"].amount == 500_000
    assert by_name["Bobur"].balance == 200_000 and by_name["Bobur"].amount == 200_000


async def test_the_amount_is_what_is_still_owed(session):
    user = await make_user(session)
    person, _ = await debt(session, user)
    await add_debt_entry(session, user_id=user.id, person_id=person.id, kind="repaid_by_me",
                         amount=200_000, currency="UZS", now=CREATED + timedelta(days=1))
    (reminder,) = await collect_debt_reminders(session, morning(DUE))
    assert reminder.amount == 300_000


async def test_closed_debts_and_debts_without_a_due_date_are_never_reminded(session):
    user = await make_user(session)
    person, _ = await debt(session, user, "Aziz")
    await add_debt_entry(session, user_id=user.id, person_id=person.id, kind="repaid_by_me",
                         amount=500_000, currency="UZS", now=CREATED + timedelta(days=1))  # closed
    await debt(session, user, "Bobur", due=None)
    assert await kinds(session, DUE) == []


async def test_currencies_are_reminded_separately(session):
    user = await make_user(session)
    await debt(session, user, "Aziz", currency="UZS", due=date(2026, 11, 25))
    await debt(session, user, "Aziz", currency="USD", amount=5_000, due=date(2026, 11, 26), hours=1)
    found = await collect_debt_reminders(session, morning(date(2026, 11, 25)))
    assert [(r.currency, r.kind) for r in found] == [("USD", ReminderKind.TOMORROW), ("UZS", ReminderKind.TODAY)]


async def test_the_newest_dated_entry_decides_the_due_date(session):
    user = await make_user(session)
    await debt(session, user, due=date(2026, 11, 25))
    await debt(session, user, due=date(2026, 12, 10), hours=2)
    assert await kinds(session, date(2026, 11, 25)) == []
    assert await kinds(session, date(2026, 12, 10)) == [ReminderKind.TODAY]


async def test_the_user_local_date_decides_not_utc(session):
    user = await make_user(session)
    await debt(session, user)
    late_evening_utc = datetime(2026, 11, 24, 20, 0, tzinfo=timezone.utc)  # 01:00 on the 25th in Tashkent
    (reminder,) = await collect_debt_reminders(session, late_evening_utc)
    assert reminder.kind is ReminderKind.TODAY


async def test_a_reminder_is_sent_once_a_day_and_overdue_ones_every_three_days(session):
    user = await make_user(session)
    _, entry = await debt(session, user)
    assert await kinds(session, DUE) == [ReminderKind.TODAY]
    await mark_reminded(session, entry.id, DUE)
    assert await kinds(session, DUE) == []  # the job ran twice the same day
    assert await kinds(session, date(2026, 11, 26)) == []
    assert await kinds(session, date(2026, 11, 27)) == []
    assert await kinds(session, date(2026, 11, 28)) == [ReminderKind.OVERDUE]


async def test_postpone_silences_the_debt_for_a_week(session):
    user = await make_user(session)
    person, _ = await debt(session, user)
    today = date(2026, 11, 28)
    assert await snooze_debt(session, user.id, person.id, "UZS", today) is True
    assert await kinds(session, date(2026, 12, 4)) == []
    assert await kinds(session, date(2026, 12, 5)) == [ReminderKind.OVERDUE]
    assert await snooze_debt(session, user.id, person.id, "USD", today) is False  # nothing in USD


async def test_changing_the_due_date_restarts_the_reminders(session):
    user = await make_user(session)
    person, entry = await debt(session, user)
    await mark_reminded(session, entry.id, DUE)
    await snooze_debt(session, user.id, person.id, "UZS", DUE)
    await set_due_date(session, user.id, person.id, "UZS", date(2026, 12, 10))
    assert await kinds(session, date(2026, 12, 9)) == [ReminderKind.TOMORROW]


async def test_debt_reminders_can_be_switched_off(session):
    user = await make_user(session)
    await debt(session, user)
    user.debt_reminders_enabled = False
    await session.flush()
    assert await kinds(session, DUE) == []
    assert await kinds(session, DUE, only_enabled=False) == [ReminderKind.TODAY]  # /remindtest


async def test_users_are_isolated_and_can_be_picked(session):
    first, second = await make_user(session, 1), await make_user(session, 2)
    await debt(session, first, "Aziz")
    await debt(session, second, "Bobur")
    both = await collect_debt_reminders(session, morning(DUE))
    assert {r.person_name for r in both} == {"Aziz", "Bobur"}
    only_first = await collect_debt_reminders(session, morning(DUE), user_id=first.id)
    assert [r.person_name for r in only_first] == ["Aziz"]


async def test_manual_test_can_pretend_it_is_another_day_and_ignore_history(session):
    user = await make_user(session)
    _, entry = await debt(session, user)
    await mark_reminded(session, entry.id, date.today())
    found = await collect_debt_reminders(session, morning(date(2026, 11, 20)), user_id=user.id,
                                         ignore_history=True, today_override=DUE)
    assert [r.kind for r in found] == [ReminderKind.TODAY]


# ------------------------------------------------------------- evening reminder
def utc(hour, minute=0, day=17):
    return datetime(2026, 11, day, hour, minute, tzinfo=timezone.utc)


async def test_the_evening_reminder_fires_at_the_chosen_local_time(session):
    user = await make_user(session)
    assert await collect_evening_reminders(session, utc(16, 0)) == []  # switched off by default
    set_reminder_time(user, time(21, 0))
    await session.flush()
    assert await collect_evening_reminders(session, utc(15, 59)) == []  # 20:59 in Tashkent
    (reminder,) = await collect_evening_reminders(session, utc(16, 0))  # 21:00
    assert (reminder.user_id, reminder.local_date) == (user.id, date(2026, 11, 17))


async def test_the_evening_reminder_is_sent_once_a_day(session):
    user = await make_user(session)
    set_reminder_time(user, time(21, 0))
    await session.flush()
    await mark_evening_sent(session, user.id, date(2026, 11, 17))
    await session.refresh(user)
    assert await collect_evening_reminders(session, utc(16, 5)) == []
    assert len(await collect_evening_reminders(session, utc(16, 5, day=18))) == 1  # next day


async def test_a_new_reminder_time_may_fire_again_today(session):
    user = await make_user(session)
    set_reminder_time(user, time(21, 0))
    await mark_evening_sent(session, user.id, date(2026, 11, 17))
    await session.refresh(user)
    set_reminder_time(user, time(21, 30))
    await session.flush()
    assert len(await collect_evening_reminders(session, utc(16, 35))) == 1


async def test_the_evening_reminder_mentions_todays_spending(session):
    await seed_default_categories(session)
    user = await make_user(session)
    food = (await list_categories(session, user.id, "expense"))[0]
    await save_transaction(session, user_id=user.id, category_id=food.id, entry_type="expense",
                           amount=45_000, currency="UZS", note=None, now=utc(10, 0))
    set_reminder_time(user, time(21, 0))
    await session.flush()
    (reminder,) = await collect_evening_reminders(session, utc(16, 0))
    assert reminder.spent_today == {"UZS": 45_000}


async def test_force_sends_even_when_the_reminder_is_off(session):
    user = await make_user(session)
    assert await collect_evening_reminders(session, utc(9, 0), user_id=user.id) == []
    assert len(await collect_evening_reminders(session, utc(9, 0), user_id=user.id, force=True)) == 1
