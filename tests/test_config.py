import pytest
from pydantic import ValidationError

from app.config import Settings, parse_user_ids


def make(**kwargs) -> Settings:
    # _env_file=None keeps a developer's real .env out of the tests
    return Settings(_env_file=None, **kwargs)


def test_parse_user_ids():
    assert parse_user_ids("") == frozenset()
    assert parse_user_ids(" 1, 2 ,3,, ") == frozenset({1, 2, 3})


def test_allowed_ids_property():
    assert make(bot_token="abc", allowed_user_ids="10,20").allowed_ids == frozenset({10, 20})
    assert make(bot_token="abc").allowed_ids == frozenset()


def test_invalid_allowed_ids_rejected():
    with pytest.raises(ValidationError):
        make(bot_token="abc", allowed_user_ids="1,abc")


def test_empty_token_rejected():
    with pytest.raises(ValidationError):
        make(bot_token="   ")


def test_token_is_required(monkeypatch):
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
