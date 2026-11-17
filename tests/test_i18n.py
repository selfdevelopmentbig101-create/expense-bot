import string

import pytest

from app.i18n import CATALOG, DEFAULT_LANGUAGE, LANGUAGES, detect_language, t


def _fields(text: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def test_all_languages_have_the_same_keys():
    reference = set(CATALOG[DEFAULT_LANGUAGE])
    for lang in LANGUAGES:
        assert set(CATALOG[lang]) == reference, f"key mismatch in {lang}"


def test_no_empty_strings():
    for lang in LANGUAGES:
        for key, text in CATALOG[lang].items():
            assert text.strip(), f"empty text for {lang}:{key}"


def test_placeholders_match_across_languages():
    for key, text in CATALOG[DEFAULT_LANGUAGE].items():
        for lang in LANGUAGES:
            assert _fields(CATALOG[lang][key]) == _fields(text), f"{lang}:{key}"


@pytest.mark.parametrize(
    "code,expected",
    [
        ("ru", "ru"),
        ("ru-RU", "ru"),
        ("uz", "uz"),
        ("uz_UZ", "uz"),
        ("en-US", "en"),
        ("de", "en"),
        (None, "en"),
        ("", "en"),
    ],
)
def test_detect_language(code, expected):
    assert detect_language(code) == expected


def test_t_formats_placeholders():
    assert "Russian" in t("en", "lang.changed", name="Russian")


def test_t_unknown_key_returns_key():
    assert t("ru", "no.such.key") == "no.such.key"


def test_t_unknown_language_falls_back_to_english():
    assert t("xx", "cat.food") == CATALOG["en"]["cat.food"]
