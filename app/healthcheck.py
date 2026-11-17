"""Docker health check: the bot touches a file every 30 seconds while its event loop is alive.

Run as `python -m app.healthcheck`: exit code 0 = healthy, 1 = not.
"""
import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path

HEARTBEAT_INTERVAL = 30
MAX_AGE = 120  # seconds without a heartbeat before the container counts as unhealthy


def heartbeat_path() -> Path:
    return Path(os.environ.get("HEARTBEAT_FILE") or Path(tempfile.gettempdir()) / "expense-bot-heartbeat")


def is_alive(path: Path, max_age: float = MAX_AGE, now: float | None = None) -> bool:
    try:
        modified = path.stat().st_mtime
    except OSError:
        return False
    return (time.time() if now is None else now) - modified <= max_age


async def heartbeat_loop(path: Path | None = None, interval: float = HEARTBEAT_INTERVAL) -> None:
    path = path or heartbeat_path()
    while True:
        try:
            path.touch()
        except OSError:
            pass  # a read-only /tmp must not take the bot down
        await asyncio.sleep(interval)


def main() -> None:
    sys.exit(0 if is_alive(heartbeat_path()) else 1)


if __name__ == "__main__":
    main()
