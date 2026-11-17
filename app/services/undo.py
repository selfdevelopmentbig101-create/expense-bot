"""/undo across income/expense records AND debt entries."""
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.debts import DebtEntryView, get_last_debt_stamp, undo_debt_entry
from app.services.transactions import (
    TransactionView,
    get_last_transaction_stamp,
    undo_transaction,
)


@dataclass(frozen=True, slots=True)
class UndoneRecord:
    transaction: TransactionView | None = None
    debt: DebtEntryView | None = None


async def undo_last(session: AsyncSession, user_id: int) -> UndoneRecord | None:
    """Delete the newest record, whichever kind it is. None if there is nothing."""
    tx = await get_last_transaction_stamp(session, user_id)
    debt = await get_last_debt_stamp(session, user_id)
    if tx is None and debt is None:
        return None

    if debt is not None and (tx is None or debt[1] >= tx[1]):
        view = await undo_debt_entry(session, user_id, debt[0])
        return UndoneRecord(debt=view) if view else None
    view = await undo_transaction(session, user_id, tx[0])
    return UndoneRecord(transaction=view) if view else None
