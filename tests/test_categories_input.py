import pytest

from app.core.categories import parse_category_input


@pytest.mark.parametrize(
    "text,expected",
    [
        ("\U0001F436 Pets", ("\U0001F436", "Pets")),
        ("Pets", (None, "Pets")),
        ("  \U0001F436   Big   dogs ", ("\U0001F436", "Big dogs")),
        ("\U0001F436", ("\U0001F436", "")),
        ("", (None, "")),
        (None, (None, "")),
        ("\U0001F1FA\U0001F1FF Uzbek", ("\U0001F1FA\U0001F1FF", "Uzbek")),  # a flag
        ("\U0001F468\u200d\U0001F469\u200d\U0001F467 Family", ("\U0001F468\u200d\U0001F469\u200d\U0001F467", "Family")),
        ("\u0415\u0434\u0430", (None, "\u0415\u0434\u0430")),  # letters are never an emoji
        ("- Pets", (None, "- Pets")),
        ("1 Pets", (None, "1 Pets")),
        ("\U0001F393Scholarship", (None, "\U0001F393Scholarship")),  # glued to a word: just a name
    ],
)
def test_parse_category_input(text, expected):
    assert parse_category_input(text) == expected
