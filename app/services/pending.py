"""Pending state between "user sent an amount" and "user tapped a button".

Stored in the database (not in memory) so it survives restarts and has a TTL.
Every user has at most one pending action: a new amount replaces the old one.
Buttons carry the token, so keyboards of replaced or expired actions stop working.
Multi-step flows (debts) move ONE pending action through several states; every
move is a conditional UPDATE, so a double tap cannot advance a step twice.
"""
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PendingAction

PENDING_TTL = timedelta(minutes=10)


class PendingState(StrEnum):
    CHOOSE_CATEGORY = "choose_category"
    CHOOSE_AMOUNT = "choose_amount"  # several amounts in one message
    CONFIRM_LARGE = "confirm_large"  # amount above 1 billion
    # --- debt flow ---
    DEBT_KIND = "debt_kind"  # borrowed / lent / repaid ...
    DEBT_PERSON = "debt_person"  # choose a person
    DEBT_NEW_NAME = "debt_new_name"  # waiting for a typed name
    DEBT_DUE = "debt_due"  # due date buttons
    DEBT_DUE_TEXT = "debt_due_text"  # waiting for a typed date
    DEBT_REPAY_AMOUNT = "debt_repay_amount"  # waiting for a typed amount (from /debts)
    DEBT_CONFIRM = "debt_confirm"  # overpayment or repayment without a debt
    # --- /categories ---
    CAT_ADD_NAME = "cat_add_name"  # waiting for the name of a new category
    CAT_RENAME_NAME = "cat_rename_name"  # waiting for a new name
    # --- /budget and /settings ---
    BUDGET_AMOUNT = "budget_amount"  # waiting for a monthly limit
    SETTINGS_TIME = "settings_time"  # waiting for the evening reminder time


DEBT_STATES = frozenset(
    {
        PendingState.DEBT_KIND,
        PendingState.DEBT_PERSON,
        PendingState.DEBT_NEW_NAME,
        PendingState.DEBT_DUE,
        PendingState.DEBT_DUE_TEXT,
        PendingState.DEBT_REPAY_AMOUNT,
        PendingState.DEBT_CONFIRM,
    }
)
# While the bot waits for one of these, the user's next text is NOT an amount to parse.
CATEGORY_TEXT_STATES = frozenset({PendingState.CAT_ADD_NAME, PendingState.CAT_RENAME_NAME})
BUDGET_TEXT_STATES = frozenset({PendingState.BUDGET_AMOUNT})
SETTINGS_TEXT_STATES = frozenset({PendingState.SETTINGS_TIME})
TEXT_STATES = frozenset(
    {
        PendingState.DEBT_NEW_NAME,
        PendingState.DEBT_DUE_TEXT,
        PendingState.DEBT_REPAY_AMOUNT,
    }
) | CATEGORY_TEXT_STATES | BUDGET_TEXT_STATES | SETTINGS_TEXT_STATES


@dataclass(frozen=True, slots=True)
class Pending:
    token: str
    state: PendingState
    payload: dict


def _now(now: datetime | None) -> datetime:
    return now or datetime.now(timezone.utc)


def _to_pending(row: PendingAction) -> Pending:
    return Pending(token=row.token, state=PendingState(row.state), payload=dict(row.payload))


async def create_pending(
    session: AsyncSession,
    user_id: int,
    state: PendingState,
    payload: dict,
    now: datetime | None = None,
) -> Pending:
    """Replace whatever the user had pending with a new action."""
    now = _now(now)
    await session.execute(delete(PendingAction).where(PendingAction.user_id == user_id))
    token = secrets.token_hex(6)  # 12 chars: short enough for callback data
    session.add(
        PendingAction(
            user_id=user_id,
            token=token,
            state=state.value,
            payload=payload,
            created_at=now,
            expires_at=now + PENDING_TTL,
        )
    )
    await session.flush()
    return Pending(token=token, state=state, payload=payload)


async def _find(session: AsyncSession, user_id: int, token: str, now: datetime) -> PendingAction | None:
    return await session.scalar(
        select(PendingAction)
        .where(
            PendingAction.user_id == user_id,
            PendingAction.token == token,
            PendingAction.expires_at > now,
        )
        .execution_options(populate_existing=True)
    )


async def get_pending(
    session: AsyncSession, user_id: int, token: str, now: datetime | None = None
) -> Pending | None:
    """Look at a pending action without using it up. None if missing or expired."""
    row = await _find(session, user_id, token, _now(now))
    return _to_pending(row) if row is not None else None


async def get_current_pending(
    session: AsyncSession, user_id: int, now: datetime | None = None
) -> Pending | None:
    """The user's live pending action, if any (used to route typed text)."""
    row = await session.scalar(
        select(PendingAction)
        .where(PendingAction.user_id == user_id, PendingAction.expires_at > _now(now))
        .order_by(PendingAction.id.desc())
        .limit(1)
        .execution_options(populate_existing=True)
    )
    return _to_pending(row) if row is not None else None


async def advance_pending(
    session: AsyncSession,
    user_id: int,
    token: str,
    *,
    expected: PendingState,
    new_state: PendingState,
    payload: dict,
    now: datetime | None = None,
) -> Pending | None:
    """Move a pending action to the next step, only if it is still in `expected`.

    Returns None when it moved already (double tap), expired or was replaced.
    Every step also restarts the 10 minute timer.
    """
    now = _now(now)
    result = await session.execute(
        update(PendingAction)
        .where(
            PendingAction.user_id == user_id,
            PendingAction.token == token,
            PendingAction.state == expected.value,
            PendingAction.expires_at > now,
        )
        .values(state=new_state.value, payload=payload, expires_at=now + PENDING_TTL)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        return None
    return Pending(token=token, state=new_state, payload=payload)


async def consume_pending(
    session: AsyncSession, user_id: int, token: str, now: datetime | None = None
) -> Pending | None:
    """Use a pending action up. Only ONE caller can win, which stops double taps."""
    row = await _find(session, user_id, token, _now(now))
    if row is None:
        return None
    data = _to_pending(row)
    result = await session.execute(delete(PendingAction).where(PendingAction.id == row.id))
    if result.rowcount != 1:  # somebody else consumed it between our SELECT and DELETE
        return None
    return data


async def purge_expired(session: AsyncSession, now: datetime | None = None) -> int:
    result = await session.execute(
        delete(PendingAction).where(PendingAction.expires_at <= _now(now))
    )
    return result.rowcount or 0
