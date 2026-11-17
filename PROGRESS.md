# PROGRESS

## Phases
- [x] Phase 0: Plan and questions (done)
- [x] Phase 1: Foundation (done)
- [x] Phase 2: Amount parser (done)
- [x] Phase 3: Expense and income flow (done)
- [x] Phase 4: Debts (done)
- [x] Phase 5: Reports, history, categories (done)
- [x] Phase 6: Budgets, reminders, settings, export (done)
- [~] Phase 7: Hardening and deployment (in review: this is the final delivery)

## Decisions log
- Stack: Python 3.11+, aiogram 3, SQLAlchemy 2 async + aiosqlite, Alembic, pytest.
- Money stored as integer minor units + currency; currencies are never mixed.
- Pending state in a DB table (`pending_actions`) with 10-minute TTL and a token on buttons.
- Double-tap protection via unique `idempotency_key` on transactions and debt entries.
- Categories with records are archived, not deleted.
- Timestamps stored in UTC (custom `UTCDateTime` type), displayed in Asia/Tashkent.
- Currencies: UZS (default), USD, EUR, RUB.
- Number rule: separator followed by exactly 3 digits = thousands, otherwise decimal.
- Debt due date: one per (person, currency), taken from the latest borrowed/lent entry.
- Budgets: recurring monthly limit per category, in the user's main currency.
- Multi-user bot; optional `ALLOWED_USER_IDS` allowlist.
- Languages: en / ru / uz (Uzbek in Latin script). Auto-detected from Telegram on first
  contact, picker under the first greeting, `/language` command. A test checks that all
  three language files have identical keys and placeholders.
- Phase 1: migrations are applied by `alembic upgrade head` (not by the bot itself);
  default categories are seeded by the bot at startup (idempotent).
- Phase 1: all tables of the spec plus `pending_actions` are created in migration 0001.
  `reminder_snoozed_until` / `last_reminded_at` for debt reminders will come in a Phase 6 migration.
- APScheduler still needs your approval before Phase 6.
- Phase 2: parser lives in `app/core/parser.py` (pure Python, no Telegram, no database).
  Result object: `ParseResult(amount, currency, type, note, error, needs_confirmation, candidates)`.
  Amount is in minor units (UZS: sums, USD/EUR/RUB: cents).
- Phase 2: with a suffix, a single dot/comma is always decimal ("1.5 mln", "1.500 mln" = 1 500 000).
  Without a suffix, separator + exactly 3 digits is thousands ("1.500" = 1500, "50.555 usd" = 50 555 USD).
- Phase 2: "m" (million) must touch the number ("1.5m"); "k", "mln" may follow one space.
- Phase 2: the same amount written twice ("10k and 10000") counts as one amount.
- Phase 2: amounts over 1 000 000 000 (major units) set `needs_confirmation`; over 1 000 000 000 000 is rejected (TOO_LARGE).
- Phase 2: several different amounts give `MULTIPLE_AMOUNTS` + up to 5 candidates (each with its own note).
- Phase 3: the "Debt" button is NOT shown yet (Phase 4 adds it). The keyboard is 8 categories + Cancel.
- Phase 3: pending state lives in `pending_actions` (10 min TTL, one per user). Buttons carry a token.
  Saving uses an atomic "consume" (DELETE + rowcount) and a unique idempotency key, so a double tap saves once.
- Phase 3: stale, replaced or double-tapped buttons only show a short toast and never edit the message
  (after a double tap the message already shows the saved record with its Undo button).
- Phase 3: amounts above 1 billion ask "Is it correct?" first; several amounts show one button per amount.
- Phase 3: notes are cut to 200 characters; /today lists the last 25 records, totals cover all of them.
- Phase 3: /today shows expenses and income (income with a +), totals per currency, never mixed.
- Phase 3: /undo deletes the newest transaction (Phase 4 adds debt entries). Undo button works until used.
- Phase 3: commands that are not built yet answer "coming soon" (handlers/fallback.py).
- Phase 4: the "Debt" button sits under EXPENSE categories only (income can never be a debt).
- Phase 4: one pending action moves through the debt states (kind, person, new name, due date, due text,
  repay amount, confirm). Every move is a conditional UPDATE, so a double tap cannot advance twice;
  every step restarts the 10 minute timer. While the bot waits for a name/date/amount, the next text is that
  answer (commands still work, Cancel leaves the flow).
- Phase 4: a NEW person is created only when the debt is saved, so cancelling leaves nothing behind.
  Undoing a person's only entry removes the person too. Names match case-insensitively (trim + collapse spaces).
- Phase 4: repayment with no matching debt (nothing owed in that direction and currency) -> warning, and the
  user can record it as the opposite NEW debt (I repaid -> I lent, they repaid -> I borrowed); the signed effect
  on the balance is identical. Overpayment -> confirmation; recorded anyway the balance flips sign.
- Phase 4: "Close debt" writes a closing repayment entry (note "closed manually", has Undo). "Delete person"
  deletes the whole history after a confirmation (no undo).
- Phase 4: due date is per (person, currency): the latest dated borrowed/lent entry. "Change due date" edits that
  entry (or the newest one if none has a date); "No deadline" clears all dates of that currency.
- Phase 4: /debts shows "You owe" and "Owed to you" blocks (a person can be in both when currencies differ)
  and a net total per currency. Person buttons: up to 30.
- Phase 4: /undo removes the newest record of ANY kind (income/expense or debt entry).
- Phase 4: `DebtKind` moved to `app/core/debts.py` (pure logic); `app.db.models.DebtKind` still works.
- Phase 5: /week = the current calendar week (Monday to Sunday), /month = the current calendar month, both in the
  user's time zone; the title shows the dates. Debts are never in reports.
- Phase 5: reports have one section per currency (never mixed), a "Spent" and an "Income" block, categories sorted
  by amount. Percentages are whole numbers that add up to exactly 100 (largest remainder). A block shows at most
  10 lines; the smallest categories are summed into "other categories".
- Phase 5: /history = the last 10 records of BOTH kinds (income/expense and debt entries), numbered, with one
  "delete" button per record. Delete is immediate (like Undo) and the list refreshes; deleting a debt entry also
  removes a person who has no entries left.
- Phase 5: /categories: built-in categories are read-only. Your own: up to 30 per type, name up to 30 characters,
  optional leading emoji ("🐶 Pets"). Names are unique per type, case-insensitive, and also against the
  built-in names in all three languages.
- Phase 5: removing a category with records HIDES it (archived: no button, records and reports keep it);
  without records it is deleted. Adding the same name again brings a hidden category back.
- Phase 5: Phase 6 budgets must treat hidden categories as not selectable.
- Phase 6: APScheduler 3.x approved and added. Two jobs: debts every day at 09:00 Asia/Tashkent (runs up to an hour
  late if the bot was down), evening reminder checked every minute.
- Phase 6: migration 0002 adds `users.last_evening_reminded_on`, `debt_entries.last_reminded_on` and
  `debt_entries.reminder_snoozed_until` (dates, not timestamps: reminders are per day). The Phase 0 names
  `reminder_snoozed_until` / `last_reminded_at` changed because a whole day is all we need. The reminder state lives
  on the entry that carries the due date, so changing the due date restarts the reminders.
- Phase 6: debt reminders: the day before and on the due date (once each), then every 3 days when overdue (with
  "Repaid" = close the debt, with Undo, and "Postpone" = 7 days). Never twice a day, never for closed debts or
  debts without a due date, both directions, one reminder per (person, currency) with the CURRENT balance.
- Phase 6: the evening reminder is optional (off by default). It is sent from the chosen time until 3 hours later,
  at most once per day, and shows today's spending.
- Phase 6: /remindtest [DD.MM.YYYY] sends YOUR reminders right now (as if today were that date), ignoring the
  "already reminded" bookkeeping and the on/off switch, recording nothing, so it can be repeated.
- Phase 6: budgets: a recurring monthly limit per expense category in the user's main currency. The warning is
  appended to the confirmation right after saving: once when spending crosses 80%, once when it reaches 100%
  (one big expense that crosses both gives only the 100% message; no nagging when already over).
- Phase 6: /settings: language, main currency (UZS/USD/EUR/RUB), evening reminder time (off / 19-22 / typed HH:MM),
  debt reminders on/off. The time zone stays Asia/Tashkent.
- Phase 6: /export sends two files: transactions and debts. UTF-8 with BOM, ';' delimiter and decimal comma (what
  Excel expects with Russian/Uzbek regional settings; with English settings use Data > From Text/CSV and pick ';').
  Text cells starting with = + - @ are prefixed with ' so Excel cannot run them as formulas.
- Phase 7: ANY error is caught by one safety net (`handlers/errors.py`): harmless Telegram errors (old button, deleted
  message, blocked bot) are only logged; real ones are logged with the full traceback and the user gets a calm
  "something went wrong, your data is safe" message in their language. The bot never stops because of one update.
- Phase 7: flood protection: 15 messages / 30 button taps per 10 seconds per user; extra updates are dropped and the
  user is told once. Double taps and rapid identical input were already safe (atomic pending, unique keys).
- Phase 7: input edge cases: stickers/voice/locations get a hint; a photo WITH a caption works like text; messages over
  1000 characters are refused politely; group chats are ignored (private chats only); forwarded messages are plain text.
- Phase 7: startup checks: a clear message and a non-zero exit code for a missing/invalid .env (2), a database that is
  not migrated (3) or a token Telegram rejects (1). `python -m app.doctor` runs the same checks step by step.
- Phase 7: bot tokens are masked in every log line and traceback. A test scans the repository for token-like strings.
- Phase 7: Docker: slim image, non-root user, only code is copied, data in the `bot-data` volume, health check
  (heartbeat file every 30 s), `restart: unless-stopped`, log rotation, graceful stop. docker-compose.yml overrides
  DATABASE_URL to the volume.
- Phase 7: backups: `python -m app.backup` uses SQLite's backup API (consistent even while the bot runs), keeps the
  newest 14 copies. README explains cron and restore.
- Phase 7: SQLite runs in WAL mode with `synchronous=NORMAL`, `busy_timeout=5000` and foreign keys on.
- Phase 7: the command menu is set per language (English by default, Russian, Uzbek).

## Known limitations (on purpose, for later)
- One time zone for everyone: Asia/Tashkent (stored per user, but there is no setting yet).
- One bot process only (long polling). Run a second copy and Telegram refuses it.
- SQLite is fine for a personal or family bot. For many users switch `DATABASE_URL` to PostgreSQL (the code is
  database-neutral; the backup tool is SQLite only).
- CSV export: all records, no date filter. Reports: calendar week/month only.
- Reminder jobs read all debts of every user with reminders on: fine for hundreds of users, not for millions.
- Uzbek is written in the Latin alphabet only.
