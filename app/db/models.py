"""All ORM models.

Money rule: amounts are integers in minor units (UZS has no minor units,
USD/EUR/RUB use cents) and always travel together with a currency code.
"""
from datetime import date, datetime, time
from enum import StrEnum

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    String,
    Text,
    Time,
    UniqueConstraint,
    false,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.debts import DebtKind  # noqa: F401  (re-exported)
from app.db.base import Base
from app.db.types import UTCDateTime, utcnow


class CategoryType(StrEnum):
    EXPENSE = "expense"
    INCOME = "income"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    language: Mapped[str] = mapped_column(String(2), default="en", server_default="en")
    currency: Mapped[str] = mapped_column(String(3), default="UZS", server_default="UZS")
    timezone: Mapped[str] = mapped_column(
        String(64), default="Asia/Tashkent", server_default="Asia/Tashkent"
    )
    # None = evening reminder is off
    reminder_time: Mapped[time | None] = mapped_column(Time)
    debt_reminders_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true()
    )
    # the day the evening reminder was last sent (at most one per day)
    last_evening_reminded_on: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint("type IN ('expense', 'income')", name="type"),
        UniqueConstraint("user_id", "name", "type", name="uq_categories_user_id_name_type"),
        Index("ix_categories_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # NULL user_id = default category shared by everyone
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # Set for default categories; used to translate the name (e.g. "cat.food")
    name_key: Mapped[str | None] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(64))
    emoji: Mapped[str] = mapped_column(String(16), default="", server_default="")
    type: Mapped[str] = mapped_column(String(10))
    sort_order: Mapped[int] = mapped_column(default=0, server_default="0")
    # Categories that already have records are archived, never deleted
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("type IN ('expense', 'income')", name="type"),
        CheckConstraint("amount > 0", name="amount_positive"),
        Index("ix_transactions_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"))
    type: Mapped[str] = mapped_column(String(10))
    amount: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    # Makes "save" safe against double taps
    idempotency_key: Mapped[str | None] = mapped_column(String(64), unique=True)


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        CheckConstraint("limit_amount > 0", name="limit_positive"),
        UniqueConstraint("user_id", "category_id", name="uq_budgets_user_id_category_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    # Recurring monthly limit, in minor units
    limit_amount: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))


class Person(Base):
    __tablename__ = "persons"
    __table_args__ = (
        UniqueConstraint("user_id", "name_normalized", name="uq_persons_user_id_name_normalized"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    # trimmed + lower-cased, used for case-insensitive matching
    name_normalized: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class DebtEntry(Base):
    __tablename__ = "debt_entries"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('borrowed', 'lent', 'repaid_by_me', 'repaid_to_me')", name="kind"
        ),
        CheckConstraint("amount > 0", name="amount_positive"),
        Index("ix_debt_entries_user_id_person_id", "user_id", "person_id"),
        Index("ix_debt_entries_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    person_id: Mapped[int] = mapped_column(ForeignKey("persons.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(16))
    amount: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    note: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[date | None] = mapped_column(Date)
    # reminder state of the entry that carries the due date
    last_reminded_on: Mapped[date | None] = mapped_column(Date)
    reminder_snoozed_until: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    idempotency_key: Mapped[str | None] = mapped_column(String(64), unique=True)


class PendingAction(Base):
    """Short-lived state between the amount message and the category tap."""

    __tablename__ = "pending_actions"
    __table_args__ = (
        Index("ix_pending_actions_user_id", "user_id"),
        Index("ix_pending_actions_expires_at", "expires_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # Short random token carried inside inline buttons; rejects stale keyboards
    token: Mapped[str] = mapped_column(String(16), unique=True)
    state: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict] = mapped_column(JSON, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
