"""Turning debts into Telegram HTML text. Names are user text, so they are escaped."""
import html
from datetime import date

from app.core.dates import format_user_date
from app.core.debts import DebtKind, Direction, direction
from app.core.money import format_amount
from app.i18n import t
from app.services.debt_flow import DebtOutcome, DebtStatus
from app.services.debts import DebtEntryView, PersonBalance
from app.services.formatting import note_suffix
from app.utils.timezone import format_date


def esc(text: str) -> str:
    return html.escape(text)


def entry_line(lang: str, kind: str, amount: int, currency: str, person_name: str) -> str:
    """"Borrowed 500 000 UZS from Aziz" (also used for Undo)."""
    return t(
        lang,
        f"debt.entry.{kind}",
        amount=format_amount(amount, currency),
        person=esc(person_name),
    )


def describe_debt_entry(lang: str, view: DebtEntryView) -> str:
    return entry_line(lang, view.kind, view.amount, view.currency, view.person_name)


def total_line(lang: str, person_name: str, balance: int, currency: str) -> str:
    """Who owes whom in total (one currency), or "closed"."""
    person = esc(person_name)
    which = direction(balance)
    if which is Direction.I_OWE:
        return t(lang, "debt.total.you_owe", person=person, total=format_amount(-balance, currency))
    if which is Direction.OWED_TO_ME:
        return t(lang, "debt.total.they_owe", person=person, total=format_amount(balance, currency))
    return t(lang, "debt.total.closed", person=person)


def render_debt_saved(lang: str, outcome: DebtOutcome) -> str:
    """The confirmation after saving, e.g.
    Borrowed 500 000 UZS from Aziz / You owe Aziz in total: 500 000 UZS / Due: 25.11.2026"""
    text = entry_line(lang, outcome.kind, outcome.amount, outcome.currency, outcome.person_name)
    text += "\n" + total_line(lang, outcome.person_name, outcome.balance, outcome.currency)
    if outcome.due is not None and outcome.balance != 0:
        text += "\n" + t(lang, "debt.due_line", date=format_user_date(outcome.due))
    return text


def render_confirm(lang: str, outcome: DebtOutcome) -> str:
    """Warning for a repayment without a matching debt, or larger than the debt."""
    by_me = outcome.kind == DebtKind.REPAID_BY_ME.value
    params = {
        "person": esc(outcome.person_name),
        "currency": outcome.currency,
        "amount": format_amount(outcome.amount, outcome.currency),
    }
    if outcome.status is DebtStatus.CONFIRM_NO_DEBT:
        return t(lang, "debt.warn.no_debt_by_me" if by_me else "debt.warn.no_debt_to_me", **params)
    return t(
        lang,
        "debt.warn.over_by_me" if by_me else "debt.warn.over_to_me",
        owed=format_amount(outcome.owed, outcome.currency),
        rest=format_amount(abs(outcome.rest), outcome.currency),
        **params,
    )


def _join(amounts: list[tuple[str, int]]) -> str:
    return ", ".join(format_amount(value, currency) for currency, value in amounts)


def render_debts(lang: str, overview: list[PersonBalance]) -> str:
    """/debts: "You owe" block, "Owed to you" block, net total per currency."""
    title = t(lang, "debts.title")
    if not overview:
        return f"{title}\n\n{t(lang, 'debts.empty')}"

    owe_lines, owed_lines = [], []
    nets: dict[str, int] = {}
    for person in overview:
        you_owe = [(c, -v) for c, v in sorted(person.balances.items()) if v < 0]
        owed_to_you = [(c, v) for c, v in sorted(person.balances.items()) if v > 0]
        if you_owe:
            owe_lines.append(f"\u2022 {esc(person.name)}: {_join(you_owe)}")
        if owed_to_you:
            owed_lines.append(f"\u2022 {esc(person.name)}: {_join(owed_to_you)}")
        for currency, value in person.balances.items():
            nets[currency] = nets.get(currency, 0) + value

    blocks = [title]
    if owe_lines:
        blocks.append(t(lang, "debts.owe_header") + "\n" + "\n".join(owe_lines))
    if owed_lines:
        blocks.append(t(lang, "debts.owed_header") + "\n" + "\n".join(owed_lines))

    net_lines = []
    for currency in sorted(nets):
        value = nets[currency]
        key = "debts.net.pos" if value > 0 else "debts.net.neg" if value < 0 else "debts.net.zero"
        net_lines.append(t(lang, key, total=format_amount(abs(value), currency)))
    blocks.append("\n".join(net_lines))
    blocks.append(t(lang, "debts.tap"))
    return "\n\n".join(blocks)


def render_person(
    lang: str,
    tz_name: str,
    person_name: str,
    balances: dict[str, int],
    dues: dict[str, date | None],
    entries: list[DebtEntryView],
) -> str:
    """One person: open balances, due dates and the latest history."""
    lines = [t(lang, "person.title", person=esc(person_name)), ""]
    open_ones = {c: v for c, v in balances.items() if v != 0}
    if not open_ones:
        lines.append(t(lang, "person.closed"))
    for currency in sorted(open_ones):
        value = open_ones[currency]
        key = "person.bal.you_owe" if value < 0 else "person.bal.they_owe"
        lines.append(t(lang, key, total=format_amount(abs(value), currency)))
        due = dues.get(currency)
        if due is not None:
            lines.append(t(lang, "person.due", currency=currency, date=format_user_date(due)))

    if entries:
        lines += ["", t(lang, "person.history")]
        for entry in entries:
            what = t(
                lang, f"debt.hist.{entry.kind}", amount=format_amount(entry.amount, entry.currency)
            )
            lines.append(
                f"{format_date(entry.created_at, tz_name)} {what}{note_suffix(entry.note)}"
            )
    return "\n".join(lines)
