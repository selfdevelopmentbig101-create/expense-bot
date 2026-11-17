from datetime import date, datetime, timezone

from app.services.debt_flow import DebtOutcome, DebtStatus
from app.services.debt_formatting import (
    describe_debt_entry,
    render_confirm,
    render_debt_saved,
    render_debts,
    render_person,
)
from app.services.debts import DebtEntryView, PersonBalance

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc)
TZ = "Asia/Tashkent"


def saved(kind, amount, balance, name="Aziz", currency="UZS", due=None):
    return DebtOutcome(
        DebtStatus.SAVED, person_name=name, kind=kind, amount=amount,
        currency=currency, balance=balance, due=due,
    )


def test_borrowed_confirmation_matches_the_spec():
    text = render_debt_saved("en", saved("borrowed", 500_000, -500_000, due=date(2026, 11, 25)))
    assert "\U0001F4E5 Borrowed 500 000 UZS from Aziz" in text
    assert "You owe Aziz in total: <b>500 000 UZS</b>" in text
    assert "Due: 25.11.2026" in text


def test_lent_confirmation():
    text = render_debt_saved("en", saved("lent", 200_000, 200_000, name="Bobur"))
    assert "\U0001F4E4 Lent 200 000 UZS to Bobur" in text
    assert "Bobur owes you in total: <b>200 000 UZS</b>" in text
    assert "Due" not in text


def test_partial_repayment_shows_what_is_left():
    text = render_debt_saved("en", saved("repaid_by_me", 200_000, -300_000))
    assert "Repaid 200 000 UZS to Aziz" in text
    assert "You owe Aziz in total: <b>300 000 UZS</b>" in text


def test_full_repayment_says_the_debt_is_closed_and_hides_the_due_date():
    text = render_debt_saved("en", saved("repaid_to_me", 300_000, 0, due=date(2026, 11, 25)))
    assert "Aziz repaid 300 000 UZS" in text
    assert "Debt with Aziz is closed" in text
    assert "Due" not in text


def test_names_are_html_escaped():
    text = render_debt_saved("en", saved("lent", 100, 100, name="<b>Al</b> & Co"))
    assert "&lt;b&gt;Al&lt;/b&gt; &amp; Co" in text and "<b>Al</b>" not in text


def test_confirm_texts():
    no_debt = DebtOutcome(DebtStatus.CONFIRM_NO_DEBT, person_name="Aziz", kind="repaid_by_me",
                          amount=100_000, currency="UZS", owed=0, rest=100_000)
    assert "don't owe Aziz anything in UZS" in render_confirm("en", no_debt)
    no_debt_to_me = DebtOutcome(DebtStatus.CONFIRM_NO_DEBT, person_name="Aziz", kind="repaid_to_me",
                                amount=100_000, currency="UZS", owed=0, rest=-100_000)
    assert "Aziz doesn't owe you anything in UZS" in render_confirm("en", no_debt_to_me)

    over = DebtOutcome(DebtStatus.CONFIRM_OVERPAY, person_name="Aziz", kind="repaid_by_me",
                       amount=150_000, currency="UZS", owed=100_000, rest=50_000)
    text = render_confirm("en", over)
    assert "only 100 000 UZS" in text and "150 000 UZS" in text and "owe you 50 000 UZS" in text
    over_to_me = DebtOutcome(DebtStatus.CONFIRM_OVERPAY, person_name="Aziz", kind="repaid_to_me",
                             amount=150_000, currency="UZS", owed=100_000, rest=-50_000)
    assert "owe Aziz 50 000 UZS" in render_confirm("en", over_to_me)


def test_debts_overview_has_two_blocks_and_a_net_total():
    overview = [
        PersonBalance(1, "Aziz", {"UZS": -500_000}),
        PersonBalance(2, "Bobur", {"UZS": 200_000}),
    ]
    text = render_debts("en", overview)
    assert "You owe:" in text and "Owed to you:" in text
    assert "\u2022 Aziz: 500 000 UZS" in text
    assert "\u2022 Bobur: 200 000 UZS" in text
    assert text.index("You owe:") < text.index("Owed to you:")
    assert "Net: you owe <b>300 000 UZS</b>" in text


def test_debts_overview_never_mixes_currencies():
    overview = [
        PersonBalance(1, "Aziz", {"UZS": -500_000, "USD": 10_000}),
        PersonBalance(2, "Bobur", {"USD": 5_000}),
    ]
    text = render_debts("en", overview)
    assert "\u2022 Aziz: 500 000 UZS" in text  # in the "you owe" block
    assert "\u2022 Aziz: 100 USD" in text  # the same person, other currency, other block
    assert "Net: owed to you <b>150 USD</b>" in text
    assert "Net: you owe <b>500 000 UZS</b>" in text


def test_only_one_block_when_there_is_only_one_direction():
    text = render_debts("en", [PersonBalance(1, "Aziz", {"UZS": -1_000})])
    assert "You owe:" in text and "Owed to you:" not in text


def test_debts_overview_when_empty():
    assert "No active debts" in render_debts("en", [])


def entry(kind, amount, minutes=0, note=None, currency="UZS"):
    return DebtEntryView(1, 1, "Aziz", kind, amount, currency, note, None, NOW.replace(minute=minutes))


def test_person_screen_with_open_debt_due_date_and_history():
    text = render_person(
        "en", TZ, "Aziz", {"UZS": -300_000}, {"UZS": date(2026, 11, 25)},
        [entry("repaid_by_me", 200_000, 5), entry("borrowed", 500_000, 0, note="for rent")],
    )
    assert "Aziz" in text
    assert "You owe: <b>300 000 UZS</b>" in text
    assert "Due (UZS): 25.11.2026" in text
    assert "17.11.2026 \U0001F4B8 You repaid 200 000 UZS" in text
    assert "Borrowed 500 000 UZS (for rent)" in text
    assert text.index("You repaid") < text.index("Borrowed")  # newest first


def test_person_screen_when_everything_is_closed():
    text = render_person("en", TZ, "Aziz", {"UZS": 0}, {}, [entry("borrowed", 100, 0)])
    assert "All debts with this person are closed" in text
    assert "You owe" not in text and "Owes you" not in text


def test_person_screen_with_two_currencies():
    text = render_person("en", TZ, "Aziz", {"UZS": -1_000, "USD": 500}, {}, [])
    assert "You owe: <b>1 000 UZS</b>" in text
    assert "Owes you: <b>5 USD</b>" in text


def test_describe_debt_entry_in_all_languages():
    view = entry("borrowed", 500_000)
    assert describe_debt_entry("en", view) == "\U0001F4E5 Borrowed 500 000 UZS from Aziz"
    assert "Aziz" in describe_debt_entry("ru", view)
    assert describe_debt_entry("uz", view) == "\U0001F4E5 Azizdan 500 000 UZS qarz oldim"
