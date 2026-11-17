"""Logging configuration. Secrets never reach the logs."""
import logging
import re

# A Telegram bot token looks like 123456789:AAH...(35 more characters)
_TOKEN_RE = re.compile(r"(?<!\d)\d{6,12}:[A-Za-z0-9_-]{30,}")  # no \b: in URLs it follows "/bot"


def redact(text: str) -> str:
    return _TOKEN_RE.sub("<bot-token>", text)


class RedactingFormatter(logging.Formatter):
    """Hides bot tokens in messages AND in tracebacks (a URL with the token can end up there)."""

    def format(self, record: logging.LogRecord) -> str:
        return redact(super().format(record))


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(
        RedactingFormatter("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
    )
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO), handlers=[handler], force=True
    )
    # Keep SQL noise out unless someone really wants it.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
