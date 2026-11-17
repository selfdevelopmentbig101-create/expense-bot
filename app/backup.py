"""Consistent backups of the SQLite database (safe while the bot is running).

    python -m app.backup            # copies data/bot.db to data/backups/bot-YYYYmmdd-HHMMSS.db

The newest 14 copies are kept. Uses SQLite's own backup API, so the copy is valid even
while the bot is writing; copying the .db file by hand is not.
"""
import sqlite3
from datetime import datetime
from pathlib import Path

from sqlalchemy.engine import make_url

KEEP_DEFAULT = 14


def sqlite_file(database_url: str) -> Path | None:
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite" or url.database in (None, "", ":memory:"):
        return None
    return Path(url.database)


def backup_database(
    db_file: Path, backup_dir: Path, keep: int = KEEP_DEFAULT, now: datetime | None = None
) -> Path:
    if keep < 1:
        raise ValueError("keep must be at least 1")
    if not db_file.exists():
        raise FileNotFoundError(f"No database at {db_file}")
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    target = backup_dir / f"bot-{stamp}.db"

    source = sqlite3.connect(db_file)
    destination = sqlite3.connect(target)
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()

    for old in sorted(backup_dir.glob("bot-*.db"))[:-keep]:
        old.unlink()
    return target


def main() -> int:
    from app.config import DatabaseSettings

    db_file = sqlite_file(DatabaseSettings().database_url)
    if db_file is None:
        print("Backups with this tool work for SQLite only. Use your database's own tools.")
        return 1
    target = backup_database(db_file, db_file.parent / "backups")
    print(f"Backup written: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
