"""The last step of the debt flow: validate, then save exactly once."""
from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import StrEnum

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.debts import (
    NEW_DEBT_KINDS,
    REPAYMENT_KINDS,
    DebtKind,
    RepaymentStatus,
    check_repayment,
    new_debt_kind_for,
)
from app.db.models import User
from app.services.debts import (
    DebtEntryView,
    add_debt_entry,
    clean_name,
    effective_due_date,
    find_person_by_name,
    get_debt_entry_view,
    get_or_create_person,
    get_person,
    get_person_balances,
)
from app.services.pending import (
    DEBT_STATES,
    PendingState,
    advance_pending,
    consume_pending,
    get_pending,
)


class DebtStatus(StrEnum):
    SAVED = "saved"
    CONFIRM_NO_DEBT = "confirm_no_debt"  # repayment but nothing to repay
    CONFIRM_OVERPAY = "confirm_overpay"  # repaying more than the debt
    STALE = "stale"  # expired, replaced, or already used (double tap)
    BAD = "bad"  # incomplete data, or the person disappeared


@dataclass(frozen=True, slots=True)
class DebtOutcome:
    status: DebtStatus
    person_name: str = ""
    kind: str = ""
    amount: int = 0
    currency: str = ""
    entry: DebtEntryView | None = None  # SAVED
    balance: int = 0  # SAVED: signed balance after saving
    due: date | None = None  # SAVED: current due date of (person, currency)
    owed: int = 0  # CONFIRM_*: size of the matching debt
    rest: int = 0  # CONFIRM_*: signed balance if recorded anyway


async def finalize_debt(
    session: AsyncSession,
    user: User,
    token: str,
    *,
    overrides: dict | None = None,
    force: bool = False,
    as_debt: bool = False,
    now: datetime | None = None,
) -> DebtOutcome:
    """Check the pending debt and save it.

    * force:   the user confirmed an overpayment.
    * as_debt: the user chose to record a repayment-without-debt as a new debt.
    * overrides: values typed later (amount, note) merged into the pending payload.
    Only one caller can ever get SAVED for a token.
    """
    now = now or datetime.now(timezone.utc)
    pending = await get_pending(session, user.id, token, now)
    if pending is None or pending.state not in DEBT_STATES:
        return DebtOutcome(DebtStatus.STALE)

    payload = {**pending.payload, **(overrides or {})}
    if force and payload.get("confirm") != "over":
        return DebtOutcome(DebtStatus.STALE)
    if as_debt and payload.get("confirm") != "no_debt":
        return DebtOutcome(DebtStatus.STALE)

    kind_raw, amount, currency = payload.get("kind"), payload.get("amount"), payload.get("currency")
    if not kind_raw or not amount or not currency:
        return DebtOutcome(DebtStatus.BAD)
    kind = DebtKind(kind_raw)

    person = None
    if payload.get("person_id"):
        person = await get_person(session, user.id, payload["person_id"])
        if person is None:
            return DebtOutcome(DebtStatus.BAD)
        person_name = person.name
    elif payload.get("person_name"):
        person = await find_person_by_name(session, user.id, payload["person_name"])
        person_name = person.name if person else clean_name(payload["person_name"])
    else:
        return DebtOutcome(DebtStatus.BAD)

    if as_debt:
        kind = new_debt_kind_for(kind)
    elif kind in REPAYMENT_KINDS and not force:
        balance = 0
        if person is not None:
            balance = (await get_person_balances(session, user.id, person.id)).get(currency, 0)
        check = check_repayment(kind, amount, balance)
        if check.status is not RepaymentStatus.OK:
            no_debt = check.status is RepaymentStatus.NO_DEBT
            moved = await advance_pending(
                session,
                user.id,
                token,
                expected=pending.state,
                new_state=PendingState.DEBT_CONFIRM,
                payload={**payload, "confirm": "no_debt" if no_debt else "over"},
                now=now,
            )
            if moved is None:
                return DebtOutcome(DebtStatus.STALE)
            return DebtOutcome(
                DebtStatus.CONFIRM_NO_DEBT if no_debt else DebtStatus.CONFIRM_OVERPAY,
                person_name=person_name,
                kind=kind.value,
                amount=amount,
                currency=currency,
                owed=check.owed,
                rest=check.rest,
            )

    # Only one concurrent tap can get past this line.
    if await consume_pending(session, user.id, token, now) is None:
        return DebtOutcome(DebtStatus.STALE)

    if person is None:
        person = await get_or_create_person(session, user.id, person_name, now)

    due = None
    if kind in NEW_DEBT_KINDS and not as_debt and payload.get("due"):
        due = date.fromisoformat(payload["due"])

    entry = await add_debt_entry(
        session,
        user_id=user.id,
        person_id=person.id,
        kind=kind,
        amount=amount,
        currency=currency,
        note=payload.get("note"),
        due_date=due,
        idempotency_key=f"pending:{token}",
        now=now,
    )
    balance = (await get_person_balances(session, user.id, person.id)).get(currency, 0)
    return DebtOutcome(
        DebtStatus.SAVED,
        person_name=person.name,
        kind=kind.value,
        amount=amount,
        currency=currency,
        entry=await get_debt_entry_view(session, user.id, entry.id),
        balance=balance,
        due=await effective_due_date(session, user.id, person.id, currency),
    )
