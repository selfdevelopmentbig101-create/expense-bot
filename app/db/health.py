"""Is the database migrated? Checked at startup so a missing step fails loudly and clearly."""
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class DatabaseNotReady(Exception):
    """The database does not match the code. The message tells the user what to run."""


def head_revision() -> str:
    """The newest migration shipped with this code."""
    config = Config()
    config.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    head = ScriptDirectory.from_config(config).get_current_head()
    assert head is not None, "no migrations found"
    return head


async def current_revision(engine: AsyncEngine) -> str | None:
    """The migration the database is at, or None if it was never migrated."""
    async with engine.connect() as connection:
        try:
            row = (await connection.execute(text("SELECT version_num FROM alembic_version"))).first()
        except DBAPIError:
            return None
    return row[0] if row else None


async def ensure_database_ready(engine: AsyncEngine) -> None:
    current, head = await current_revision(engine), head_revision()
    if current is None:
        raise DatabaseNotReady("The database has not been created yet. Run:  alembic upgrade head")
    if current != head:
        raise DatabaseNotReady(
            f"The database is at version {current} but this code needs {head}. "
            "Run:  alembic upgrade head"
        )
