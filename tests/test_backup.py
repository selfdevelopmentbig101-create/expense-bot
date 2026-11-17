import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.backup import backup_database, sqlite_file


def make_db(path: Path, rows=("a", "b", "c")) -> None:
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE notes (text TEXT)")
    connection.executemany("INSERT INTO notes VALUES (?)", [(r,) for r in rows])
    connection.commit()
    connection.close()


def read(path: Path) -> list[str]:
    connection = sqlite3.connect(path)
    try:
        return [r[0] for r in connection.execute("SELECT text FROM notes ORDER BY rowid")]
    finally:
        connection.close()


def test_sqlite_file_from_a_database_url():
    assert sqlite_file("sqlite+aiosqlite:///./data/bot.db") == Path("./data/bot.db")
    assert sqlite_file("sqlite+aiosqlite:////app/data/bot.db") == Path("/app/data/bot.db")
    assert sqlite_file("sqlite+aiosqlite:///:memory:") is None
    assert sqlite_file("postgresql+asyncpg://u:p@host/db") is None


def test_the_backup_is_a_complete_copy(tmp_path):
    db = tmp_path / "bot.db"
    make_db(db)
    target = backup_database(db, tmp_path / "backups")
    assert target.parent == tmp_path / "backups" and target.name.startswith("bot-")
    assert read(target) == ["a", "b", "c"]


def test_the_backup_works_while_the_bot_has_the_database_open_in_wal_mode(tmp_path):
    db = tmp_path / "bot.db"
    make_db(db)
    live = sqlite3.connect(db)  # the running bot
    live.execute("PRAGMA journal_mode=WAL")
    live.execute("INSERT INTO notes VALUES ('newest')")
    live.commit()
    try:
        target = backup_database(db, tmp_path / "backups")
    finally:
        live.close()
    assert read(target)[-1] == "newest"  # data that still sits in the WAL file is included


def test_only_the_newest_backups_are_kept(tmp_path):
    db = tmp_path / "bot.db"
    make_db(db)
    start = datetime(2026, 11, 1, 3, 0, 0)
    made = [backup_database(db, tmp_path / "b", keep=3, now=start + timedelta(days=i)) for i in range(6)]
    left = sorted(p.name for p in (tmp_path / "b").glob("bot-*.db"))
    assert left == sorted(p.name for p in made[-3:])


def test_bad_arguments(tmp_path):
    with pytest.raises(FileNotFoundError):
        backup_database(tmp_path / "nope.db", tmp_path / "b")
    db = tmp_path / "bot.db"
    make_db(db)
    with pytest.raises(ValueError):
        backup_database(db, tmp_path / "b", keep=0)
