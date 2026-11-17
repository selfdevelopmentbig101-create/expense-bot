"""Tiny translation layer: English, Russian, Uzbek (Latin)."""
import logging

from app.i18n import en, ru, uz

logger = logging.getLogger(__name__)

LANGUAGES = ("en", "ru", "uz")
DEFAULT_LANGUAGE = "en"
LANGUAGE_NAMES = {"en": "English", "ru": "Русский", "uz": "O'zbekcha"}

CATALOG: dict[str, dict[str, str]] = {"en": en.STRINGS, "ru": ru.STRINGS, "uz": uz.STRINGS}


def detect_language(language_code: str | None) -> str:
    """Map a Telegram language_code ("ru", "uz-UZ", "en_US") to a supported one."""
    if not language_code:
        return DEFAULT_LANGUAGE
    base = language_code.lower().replace("_", "-").split("-")[0]
    return base if base in LANGUAGES else DEFAULT_LANGUAGE


def t(lang: str, key: str, **kwargs: object) -> str:
    """Translate a key. Falls back to English, then to the key itself."""
    text = CATALOG.get(lang, {}).get(key)
    if text is None:
        text = CATALOG[DEFAULT_LANGUAGE].get(key)
    if text is None:
        logger.error("Missing translation key: %s", key)
        return key
    return text.format(**kwargs) if kwargs else text
