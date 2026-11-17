"""Alembic environment (async). The database URL comes from DATABASE_URL / .env."""
import asyncio

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import DatabaseSettings
from app.db import models  # noqa: F401  (registers tables on the metadata)
from app.db.base import Base
from app.db.session import ensure_sqlite_dir

config = context.config
target_metadata = Base.metadata


def get_url() -> str:
    # An explicit URL (for example from tests) wins over the environment.
    return config.get_main_option("sqlalchemy.url") or DatabaseSettings().database_url


def run_migrations_offline() -> None:
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    url = get_url()
    ensure_sqlite_dir(url)
    connectable = async_engine_from_config(
        {"sqlalchemy.url": url}, poolclass=pool.NullPool
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
