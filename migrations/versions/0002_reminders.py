"""Reminder bookkeeping

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # the day the evening reminder was last sent (at most one per day)
    op.add_column("users", sa.Column("last_evening_reminded_on", sa.Date(), nullable=True))
    # reminder state lives on the entry that carries the due date
    op.add_column("debt_entries", sa.Column("last_reminded_on", sa.Date(), nullable=True))
    op.add_column("debt_entries", sa.Column("reminder_snoozed_until", sa.Date(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("debt_entries") as batch:
        batch.drop_column("reminder_snoozed_until")
        batch.drop_column("last_reminded_on")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("last_evening_reminded_on")
