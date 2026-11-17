import logging
import sys

from app.logging_setup import RedactingFormatter, redact

TOKEN = "123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw"  # a made-up token


def test_a_token_is_hidden():
    assert redact(f"GET https://api.telegram.org/bot{TOKEN}/getMe failed") == (
        "GET https://api.telegram.org/bot<bot-token>/getMe failed"
    )
    assert TOKEN not in redact(f"token={TOKEN}")


def test_normal_text_is_left_alone():
    for text in ("12:30", "time 10:30:45 UTC", "user 123456789 sent 10000", "a:b", ""):
        assert redact(text) == text


def test_tracebacks_are_cleaned_too():
    try:
        raise RuntimeError(f"request to /bot{TOKEN}/sendMessage failed")
    except RuntimeError:
        record = logging.LogRecord("x", logging.ERROR, "f.py", 1, "boom %s", ("now",), sys.exc_info())
    formatted = RedactingFormatter("%(message)s").format(record)
    assert "boom now" in formatted and "RuntimeError" in formatted
    assert TOKEN not in formatted and "<bot-token>" in formatted
