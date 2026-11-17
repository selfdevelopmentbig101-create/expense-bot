"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-11-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("language", sa.String(length=2), server_default="en", nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="UZS", nullable=False),
        sa.Column(
            "timezone", sa.String(length=64), server_default="Asia/Tashkent", nullable=False
        ),
        sa.Column("reminder_time", sa.Time(), nullable=True),
        sa.Column(
            "debt_reminders_enabled", sa.Boolean(), server_default=sa.true(), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("telegram_id", name=op.f("uq_users_telegram_id")),
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("name_key", sa.String(length=64), nullable=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("emoji", sa.String(length=16), server_default="", nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.CheckConstraint("type IN ('expense', 'income')", name=op.f("ck_categories_type")),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_categories_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.UniqueConstraint("name_key", name=op.f("uq_categories_name_key")),
        sa.UniqueConstraint(
            "user_id", "name", "type", name=op.f("uq_categories_user_id_name_type")
        ),
    )
    op.create_index(op.f("ix_categories_user_id"), "categories", ["user_id"], unique=False)

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=True),
        sa.CheckConstraint("type IN ('expense', 'income')", name=op.f("ck_transactions_type")),
        sa.CheckConstraint("amount > 0", name=op.f("ck_transactions_amount_positive")),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_transactions_category_id_categories"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_transactions_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transactions")),
        sa.UniqueConstraint("idempotency_key", name=op.f("uq_transactions_idempotency_key")),
    )
    op.create_index(
        op.f("ix_transactions_user_id_created_at"),
        "transactions",
        ["user_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "budgets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("limit_amount", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.CheckConstraint("limit_amount > 0", name=op.f("ck_budgets_limit_positive")),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_budgets_category_id_categories"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_budgets_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_budgets")),
        sa.UniqueConstraint("user_id", "category_id", name=op.f("uq_budgets_user_id_category_id")),
    )

    op.create_table(
        "persons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("name_normalized", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_persons_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_persons")),
        sa.UniqueConstraint(
            "user_id", "name_normalized", name=op.f("uq_persons_user_id_name_normalized")
        ),
    )

    op.create_table(
        "debt_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("person_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=True),
        sa.CheckConstraint(
            "kind IN ('borrowed', 'lent', 'repaid_by_me', 'repaid_to_me')",
            name=op.f("ck_debt_entries_kind"),
        ),
        sa.CheckConstraint("amount > 0", name=op.f("ck_debt_entries_amount_positive")),
        sa.ForeignKeyConstraint(
            ["person_id"],
            ["persons.id"],
            name=op.f("fk_debt_entries_person_id_persons"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_debt_entries_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_debt_entries")),
        sa.UniqueConstraint("idempotency_key", name=op.f("uq_debt_entries_idempotency_key")),
    )
    op.create_index(
        op.f("ix_debt_entries_user_id_person_id"),
        "debt_entries",
        ["user_id", "person_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_debt_entries_user_id_created_at"),
        "debt_entries",
        ["user_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "pending_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=16), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_pending_actions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pending_actions")),
        sa.UniqueConstraint("token", name=op.f("uq_pending_actions_token")),
    )
    op.create_index(
        op.f("ix_pending_actions_user_id"), "pending_actions", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_pending_actions_expires_at"), "pending_actions", ["expires_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_pending_actions_expires_at"), table_name="pending_actions")
    op.drop_index(op.f("ix_pending_actions_user_id"), table_name="pending_actions")
    op.drop_table("pending_actions")
    op.drop_index(op.f("ix_debt_entries_user_id_created_at"), table_name="debt_entries")
    op.drop_index(op.f("ix_debt_entries_user_id_person_id"), table_name="debt_entries")
    op.drop_table("debt_entries")
    op.drop_table("persons")
    op.drop_table("budgets")
    op.drop_index(op.f("ix_transactions_user_id_created_at"), table_name="transactions")
    op.drop_table("transactions")
    op.drop_index(op.f("ix_categories_user_id"), table_name="categories")
    op.drop_table("categories")
    op.drop_table("users")
