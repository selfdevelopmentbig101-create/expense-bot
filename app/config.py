"""Settings loaded from environment variables and the .env file."""
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATABASE_URL = "sqlite+aiosqlite:///./data/bot.db"


def parse_user_ids(raw: str) -> frozenset[int]:
    """Parse "1, 2,3" into frozenset({1, 2, 3}). Empty string gives an empty set."""
    ids = [part.strip() for part in raw.split(",") if part.strip()]
    return frozenset(int(part) for part in ids)


class DatabaseSettings(BaseSettings):
    """Only the database part, so Alembic works without a bot token."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = DEFAULT_DATABASE_URL


class Settings(DatabaseSettings):
    bot_token: str
    log_level: str = "INFO"
    # Comma separated Telegram ids. Empty means the bot is open to everyone.
    allowed_user_ids: str = ""

    @field_validator("bot_token")
    @classmethod
    def _token_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("BOT_TOKEN must not be empty")
        return value

    @field_validator("allowed_user_ids")
    @classmethod
    def _ids_are_numbers(cls, value: str) -> str:
        try:
            parse_user_ids(value)
        except ValueError as exc:
            raise ValueError(
                "ALLOWED_USER_IDS must be comma separated numbers"
            ) from exc
        return value

    @property
    def allowed_ids(self) -> frozenset[int]:
        return parse_user_ids(self.allowed_user_ids)


@lru_cache
def get_settings() -> Settings:
    return Settings()
