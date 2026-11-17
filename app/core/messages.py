"""Reading incoming messages. Works with any object that has .text / .caption."""

MAX_TEXT_LENGTH = 1000  # longer messages are refused politely


def message_text(message) -> str | None:
    """The text of a message, or the caption of a photo/document sent with a note."""
    return getattr(message, "text", None) or getattr(message, "caption", None)


def is_plain_text(message) -> bool:
    """True for text (or a caption) that is not a /command."""
    text = getattr(message, "text", None)
    if text is not None and text.startswith("/"):
        return False
    return bool(message_text(message))
