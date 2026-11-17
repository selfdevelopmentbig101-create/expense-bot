# Expense Bot

A Telegram bot that tracks your **expenses, income and debts** in two taps: send an amount, tap a
category. It speaks **English, Russian and Uzbek**.

```
you:  10000 bread          bot:  [Food] [Transport] [Home] ...
you:  (tap Food)           bot:  \u2705 10 000 UZS \u2014 Food (bread). Spent today: 45 000 UZS   [Undo]
```

Amounts: `10000`, `10.000`, `12 500`, `1,500,000`, `10k`, `1.5 mln`, `50 usd`, `$50`.
Start with `+` for income: `+2000000 salary`. After an amount tap **\U0001F91D Debt** for borrowed / lent / repaid.

## What you need

* A Telegram account.
* Python 3.11 or newer (to run on your computer) **or** Docker (to run on a server).
* About 10 minutes.

## 1. Create the bot in Telegram

1. Open Telegram and start a chat with **@BotFather** (the official bot with a blue check mark).
2. Send `/newbot`.
3. Send a **name** (shown in chats, for example `My Expenses`).
4. Send a **username** that ends in `bot` (for example `my_expenses_123_bot`). It must be unique.
5. BotFather answers with a **token** like `123456789:AAH...`. Copy it. It is the key to your bot:
   never post it or commit it. If it leaks, send `/revoke` to @BotFather to get a new one.

Nothing else is needed in BotFather: the bot sets its own command menu when it starts.

## 2. (Optional) Make the bot private

By default anyone who finds your bot can use it (everybody gets their own separate data).
To allow only yourself: send any message to **@userinfobot**, copy the number it shows (your id) and
put it into `ALLOWED_USER_IDS` in step 3. Several people: `ALLOWED_USER_IDS=111111,222222`.

## 3. Run it on your computer

```bash
# in the project folder
python -m venv .venv
source .venv/bin/activate            # Windows (PowerShell):  .venv\Scripts\Activate.ps1
pip install -r requirements.txt

cp .env.example .env                 # Windows: copy .env.example .env
# open .env in an editor and set BOT_TOKEN=... (and ALLOWED_USER_IDS if you want)

python -m app.doctor                 # checks everything and tells you what is missing
alembic upgrade head                 # creates the database (data/bot.db)
python -m app.doctor                 # all lines should now say [ OK ]
python -m app                        # starts the bot; stop it with Ctrl+C
```

If `python -m app.doctor` shows `[FAIL]`, read the line: it says what to do.

## 4. Try it in Telegram

1. Open your bot and send `/start`. Pick your language with the buttons under the guide.
2. Send `10000 bread`, tap **Food**. You get a confirmation with **Undo**. Check `/today`.
3. Send `+2000000 salary` and pick **Salary**. Check `/week` and `/month`.
4. Send `500000`, tap **\U0001F91D Debt**, **I borrowed**, **New person**, type a name, choose a due date. Check `/debts`.
5. Try `/budget`, `/categories`, `/history`, `/settings`, `/export`.
6. Reminders: send `/remindtest` (reminders for your debts and the evening check-in, right now) or
   `/remindtest 24.11.2026` to pretend that today is that date. Nothing is recorded, so repeat it freely.

## 5. Run it on a server (VPS) with Docker

A small VPS (1 CPU, 512 MB) is enough. Ubuntu/Debian is assumed.

```bash
# 1. Install Docker (once). See https://docs.docker.com/engine/install/ for your system.
curl -fsSL https://get.docker.com | sh

# 2. Put the project on the server (git clone, or upload and unzip it), then:
cd expense-bot
cp .env.example .env
nano .env                            # set BOT_TOKEN (and ALLOWED_USER_IDS)

# 3. Build and start (it restarts by itself after a reboot or a crash)
docker compose up -d --build

# 4. Check
docker compose ps                    # STATUS should become "healthy" within a minute
docker compose logs -f bot           # look for: Starting @your_bot_name
```

The database lives in the Docker volume `bot-data`, so rebuilding or updating never deletes it.
`docker compose down` stops the bot and keeps the data; `docker compose down -v` **deletes the data**.

**Only one copy of the bot may run per token.** If you also run it on your computer, stop that one,
otherwise Telegram answers with `Conflict: terminated by other getUpdates request`.

### Updating

```bash
# replace the project files with the new version (keep your .env), then:
docker compose up -d --build         # the database is upgraded automatically on start
```

## 6. Backups (do this!)

Your whole history is one file. Make a copy regularly:

```bash
# one backup now (a consistent copy, safe while the bot is running)
docker compose exec -T bot python -m app.backup
#   -> /app/data/backups/bot-YYYYmmdd-HHMMSS.db   (the newest 14 are kept)

# copy the backups out of the container, to a place that is NOT this server (laptop, cloud storage)
docker compose cp bot:/app/data/backups ./backups
```

Every night at 03:00, from the server's crontab (`crontab -e`):

```
0 3 * * * cd /path/to/expense-bot && docker compose exec -T bot python -m app.backup >> backup.log 2>&1
```

Without Docker: `python -m app.backup` writes into `data/backups/`.

**Restore** (replace the file name):

```bash
docker compose stop bot
docker compose run --rm --no-deps bot sh -c "rm -f /app/data/bot.db-wal /app/data/bot.db-shm && cp /app/data/backups/bot-20261117-030000.db /app/data/bot.db"
docker compose start bot
```

## 7. Commands

| Command | What it does |
|---|---|
| `/start`, `/language` | guide, choose English / Russian / Uzbek |
| *(an amount)* | start a record: `10000 bread`, `+2000000`, `50 usd` |
| `/today`, `/week`, `/month` | records and totals; week and month have a breakdown with percentages |
| `/history` | last 10 records, each with a delete button |
| `/undo` | delete the newest record (expense, income or debt entry) |
| `/debts` | who owes whom; open a person to repay, change the due date, close or delete |
| `/categories` | add, rename, remove your own categories |
| `/budget` | monthly limit per category; warnings at 80% and 100% |
| `/settings` | language, main currency, evening reminder, debt reminders |
| `/export` | CSV files: income and expenses, and debts (open them in Excel) |
| `/remindtest [DD.MM.YYYY]` | send your reminders now, for testing |

## 8. Settings (.env)

| Variable | Meaning |
|---|---|
| `BOT_TOKEN` | Required. The token from @BotFather. |
| `ALLOWED_USER_IDS` | Optional. Comma separated Telegram ids. Empty = anyone can use the bot. |
| `LOG_LEVEL` | `INFO` (default), `DEBUG` for more detail. |
| `DATABASE_URL` | Default `sqlite+aiosqlite:///./data/bot.db`. In Docker it is fixed to the volume. |

## 9. Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## 10. Troubleshooting

| Problem | Fix |
|---|---|
| `Configuration problem: bot_token: Field required` | You did not create `.env` or did not set `BOT_TOKEN`. |
| `Telegram rejected BOT_TOKEN` | The token is wrong or was revoked. Copy it again from @BotFather. |
| `The database has not been created yet` / `... needs 000X` | Run `alembic upgrade head` (Docker does it for you). |
| `Conflict: terminated by other getUpdates request` | Another copy of the bot runs with the same token. Stop it. |
| The bot does not answer | `docker compose logs -f bot` (or the terminal). Check `ALLOWED_USER_IDS` includes your id. |
| Reminders come at a strange hour | Times use **Asia/Tashkent** (09:00 for debts). The evening reminder uses the time you set in `/settings`. |
| The CSV is one column in Excel | In Excel use *Data > From Text/CSV* and choose `;` as the delimiter. |
| `docker compose ps` says `unhealthy` | The bot is stuck or crashed: read `docker compose logs bot`. |

## Notes

* Amounts are stored as whole numbers (UZS has no cents; USD, EUR, RUB use cents). Currencies are never mixed.
* Times are stored in UTC and shown in Asia/Tashkent.
* A user who sends more than 15 messages in 10 seconds is told to slow down for a moment.
* Messages that are not text (stickers, voice ...) get a short hint; a photo with a caption works like text.
