import asyncio
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from app.db.health import DatabaseNotReady, current_revision, ensure_database_ready, head_revision
from app.db.session import create_engine

ROOT = Path(__file__).resolve().parent.parent


def alembic_config(db_file: Path) -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{db_file}")
    return cfg


async def test_a_fully_migrated_database_is_ready(tmp_path):
    db_file = tmp_path / "ok.db"
    await asyncio.to_thread(command.upgrade, alembic_config(db_file), "head")
    engine = create_engine(f"sqlite+aiosqlite:///{db_file}")
    try:
        assert await current_revision(engine) == head_revision()
        await ensure_database_ready(engine)  # does not raise
    finally:
        await engine.dispose()


async def test_an_empty_database_tells_the_user_what_to_run(tmp_path):
    engine = create_engine(f"sqlite+aiosqlite:///{tmp_path / 'empty.db'}")
    try:
        assert await current_revision(engine) is None
        with pytest.raises(DatabaseNotReady, match="alembic upgrade head"):
            await ensure_database_ready(engine)
    finally:
        await engine.dispose()


async def test_an_outdated_database_is_refused(tmp_path):
    db_file = tmp_path / "old.db"
    await asyncio.to_thread(command.upgrade, alembic_config(db_file), "0001")
    engine = create_engine(f"sqlite+aiosqlite:///{db_file}")
    try:
        assert await current_revision(engine) == "0001"
        with pytest.raises(DatabaseNotReady, match="0001"):
            await ensure_database_ready(engine)
    finally:
        await engine.dispose()
