import pytest

from app.core.errors import is_benign_telegram_error


@pytest.mark.parametrize(
    "message",
    [
        "Telegram server says - Bad Request: message is not modified: specified new message content ...",
        "Bad Request: query is too old and response timeout expired or query ID is invalid",
        "Bad Request: message to edit not found",
        "Forbidden: bot was blocked by the user",
        "Bad Request: chat not found",
        "BAD REQUEST: MESSAGE IS NOT MODIFIED",
    ],
)
def test_harmless_errors(message):
    assert is_benign_telegram_error(message) is True


@pytest.mark.parametrize(
    "message",
    ["", None, "database is locked", "Bad Request: can't parse entities", "Unauthorized"],
)
def test_real_errors_are_not_hidden(message):
    assert is_benign_telegram_error(message) is False
