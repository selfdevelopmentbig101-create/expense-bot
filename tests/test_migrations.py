"""Runs the real Alembic migration on an empty SQLite file.

These tests are plain (sync) functions on purpose: env.py starts its own event loop.
"""
from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.db import models  # noqa: F401
from app.db.base import Base

ROOT = Path(__file__).resolve().parent.parent


def _config(db_file: Path) -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite+aiosqlite:///{db_file}")
    return cfg


def test_upgrade_matches_the_models(tmp_path):
    db_file = tmp_path / "migrated.db"
    command.upgrade(_config(db_file), "head")

    inspector = sa.inspect(sa.create_engine(f"sqlite:///{db_file}"))
    tables = set(inspector.get_table_names()) - {"alembic_version"}
    assert tables == set(Base.metadata.tables)

    for name, table in Base.metadata.tables.items():
        db_columns = {c["name"] for c in inspector.get_columns(name)}
        assert db_columns == {c.name for c in table.columns}, name
        db_indexes = {i["name"] for i in inspector.get_indexes(name)}
        assert db_indexes == {i.name for i in table.indexes}, name


def test_downgrade_removes_everything(tmp_path):
    db_file = tmp_path / "down.db"
    cfg = _config(db_file)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")

    inspector = sa.inspect(sa.create_engine(f"sqlite:///{db_file}"))
    assert set(inspector.get_table_names()) - {"alembic_version"} == set()
