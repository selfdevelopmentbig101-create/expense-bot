"""Which Telegram errors are harmless. Pure logic."""

# Normal things in a chat app: an old button, a message the user deleted, a blocked bot.
_BENIGN_MARKERS = (
    "message is not modified",
    "query is too old",
    "query id is invalid",
    "message to edit not found",
    "message can't be edited",
    "message to delete not found",
    "bot was blocked by the user",
    "user is deactivated",
    "chat not found",
)


def is_benign_telegram_error(message: str) -> bool:
    text = (message or "").lower()
    return any(marker in text for marker in _BENIGN_MARKERS)
