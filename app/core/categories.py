"""Parsing what the user types when adding or renaming a category. Pure logic."""
import re

MAX_CATEGORY_NAME = 30
MAX_CUSTOM_PER_TYPE = 30
DEFAULT_CATEGORY_EMOJI = "\U0001F3F7"  # label


def _is_emoji_token(token: str) -> bool:
    """A short word made only of non-ASCII symbols, e.g. a dog or a graduation cap."""
    return (
        0 < len(token) <= 8
        and all(ord(char) > 127 for char in token)
        and not any(char.isalnum() for char in token)
    )


def parse_category_input(text: str) -> tuple[str | None, str]:
    """"\U0001F436 Pets" -> (emoji, "Pets"); "Pets" -> (None, "Pets").

    The name is trimmed and inner whitespace is collapsed. It may come back empty.
    """
    text = (text or "").strip()
    parts = text.split(None, 1)
    if parts and _is_emoji_token(parts[0]):
        rest = parts[1] if len(parts) == 2 else ""
        return parts[0], re.sub(r"\s+", " ", rest).strip()
    return None, re.sub(r"\s+", " ", text).strip()
