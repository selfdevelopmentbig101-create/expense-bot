STRINGS = {
    "start.guide": (
        "👋 Hi! I help you track expenses, income and debts.\n\n"
        "Send an amount, then tap a category:\n"
        "• <code>10000 bread</code>\n"
        "• <code>10k</code>\n"
        "• <code>1.5 mln</code>\n"
        "• <code>50 usd</code>\n\n"
        "Income starts with +: <code>+2000000</code>\n"
        "Debts: send an amount, then tap 🤝 Debt.\n\n"
        "Commands:\n"
        "/today, /week, /month — reports\n"
        "/history, /undo — history and undo\n"
        "/debts — debts\n"
        "/categories, /budget — categories and budgets\n"
        "/export, /settings — export and settings\n"
        "/language — change language"
    ),
    "lang.hint": "🌐 Language:",
    "lang.choose": "🌐 Choose your language:",
    "lang.changed": "✅ Language: {name}",
    "access.denied": "⛔ Sorry, this bot is private.",
    "cat.food": "Food",
    "cat.transport": "Transport",
    "cat.home": "Home",
    "cat.health": "Health",
    "cat.clothes": "Clothes",
    "cat.fun": "Fun",
    "cat.phone_internet": "Phone/Internet",
    "cat.other": "Other",
    "cat.salary": "Salary",
    "cat.gift": "Gift",
    "cat.other_income": "Other income",
    # --- Phase 3: expense / income flow ---
    "amount.help": (
        "🤔 I couldn't find an amount in your message.\n\n"
        "Try something like:\n"
        "• <code>10000</code>\n"
        "• <code>10k bread</code>\n"
        "• <code>+2000000 salary</code>\n"
        "• <code>50 usd</code>"
    ),
    "amount.zero": "The amount must be greater than zero. Example: <code>10000</code>",
    "amount.decimals": (
        "🔢 Too many decimal places. UZS has none, USD, EUR and RUB allow 2. "
        "Please check the number."
    ),
    "amount.too_large": "🔢 That amount is too large. Please send a smaller one.",
    "multi.ask": "🔢 I found several amounts. Which one should I use?",
    "large.confirm": "⚠️ That's a very large amount: <b>{amount}</b>. Is it correct?",
    "pending.expense": "💸 <b>{amount}</b>{note}\nChoose a category:",
    "pending.income": "💰 <b>+{amount}</b>{note}\nChoose a category:",
    "btn.cancel": "❌ Cancel",
    "btn.undo": "↩️ Undo",
    "btn.large_ok": "✅ Yes, correct",
    "saved.expense": "✅ {amount} — {category}{note}. Spent today: {total}",
    "saved.income": "✅ +{amount} — {category}{note}. Income today: {total}",
    "undo.done": "↩️ Cancelled: {summary}",
    "undo.nothing": "Nothing to undo.",
    "undo.already": "Already undone.",
    "expired": "⌛ Already used or expired. Send the amount again.",
    "cancelled": "❌ Cancelled.",
    "today.title": "📅 <b>Today, {date}</b>",
    "today.empty": "No records today yet. Send an amount to add one.",
    "today.spent": "Spent: <b>{total}</b>",
    "today.income": "Income: <b>{total}</b>",
    "today.more": "…and {count} earlier",
    "cmd.soon": "🚧 This command is coming soon.",
    # --- Phase 4: debts ---
    "debt.btn": "🤝 Debt",
    "debt.kind.borrowed": "📥 I borrowed",
    "debt.kind.lent": "📤 I lent",
    "debt.kind.repaid_by_me": "💸 I repaid",
    "debt.kind.repaid_to_me": "✅ They repaid me",
    "debt.kind.prompt": "🤝 <b>{amount}</b>{note}\nWhat happened?",
    "debt.person.prompt": "{kind} · <b>{amount}</b>\n👤 Choose a person:",
    "debt.person.new": "➕ New person",
    "debt.person.ask_name": "✍️ Type the person's name:",
    "debt.person.name_invalid": "Please send a name (text, up to 100 characters).",
    "debt.person.gone": "This person no longer exists.",
    "debt.due.prompt": "{kind} · <b>{amount}</b> · 👤 {person}\n📅 When should it be returned?",
    "debt.due.none": "No deadline",
    "debt.due.w1": "In 1 week",
    "debt.due.m1": "In 1 month",
    "debt.due.pick": "Pick a date",
    "debt.due.ask_date": "📅 Send the date as DD.MM.YYYY, for example <code>{example}</code>:",
    "debt.due.invalid": "I couldn't read that date. Please use DD.MM.YYYY, for example <code>{example}</code>.",
    "debt.due.past": "That date is in the past. Please send today's date or a later one.",
    "debt.due.change_prompt": "📅 New due date for {person} ({currency}):",
    "debt.due.changed": "📅 Due date for {person} ({currency}): {date}",
    "debt.due.removed": "📅 Deadline removed for {person} ({currency}).",
    "debt.entry.borrowed": "📥 Borrowed {amount} from {person}",
    "debt.entry.lent": "📤 Lent {amount} to {person}",
    "debt.entry.repaid_by_me": "💸 Repaid {amount} to {person}",
    "debt.entry.repaid_to_me": "✅ {person} repaid {amount}",
    "debt.total.you_owe": "You owe {person} in total: <b>{total}</b>",
    "debt.total.they_owe": "{person} owes you in total: <b>{total}</b>",
    "debt.total.closed": "✅ Debt with {person} is closed.",
    "debt.due_line": "📅 Due: {date}",
    "debt.warn.no_debt_by_me": (
        "⚠️ You don't owe {person} anything in {currency}. "
        "Record {amount} as money you lent them instead?"
    ),
    "debt.warn.no_debt_to_me": (
        "⚠️ {person} doesn't owe you anything in {currency}. "
        "Record {amount} as money you borrowed from them instead?"
    ),
    "debt.warn.over_by_me": (
        "⚠️ You owe {person} only {owed}, but you are repaying {amount}. "
        "Record anyway? {person} would then owe you {rest}."
    ),
    "debt.warn.over_to_me": (
        "⚠️ {person} owes you only {owed}, but they repaid {amount}. "
        "Record anyway? You would then owe {person} {rest}."
    ),
    "debt.btn.as_debt": "✅ Yes, record as debt",
    "debt.btn.anyway": "✅ Record anyway",
    "debt.repay.prompt_by_me": (
        "💸 How much did you repay to {person}? You owe: <b>{owed}</b>\n"
        "Send an amount (for example <code>100k</code>) or tap the full amount."
    ),
    "debt.repay.prompt_to_me": (
        "✅ How much did {person} repay? They owe you: <b>{owed}</b>\n"
        "Send an amount (for example <code>100k</code>) or tap the full amount."
    ),
    "debt.repay.full": "Full: {amount}",
    "debt.repay.wrong_currency": "Please send the amount in {currency}.",
    "debts.title": "🤝 <b>Debts</b>",
    "debts.owe_header": "<b>You owe:</b>",
    "debts.owed_header": "<b>Owed to you:</b>",
    "debts.empty": "No active debts. Send an amount and tap 🤝 Debt to record one.",
    "debts.net.pos": "Net: owed to you <b>{total}</b>",
    "debts.net.neg": "Net: you owe <b>{total}</b>",
    "debts.net.zero": "Net: <b>{total}</b>",
    "debts.tap": "Tap a person for details:",
    "person.title": "👤 <b>{person}</b>",
    "person.bal.you_owe": "You owe: <b>{total}</b>",
    "person.bal.they_owe": "Owes you: <b>{total}</b>",
    "person.closed": "✅ All debts with this person are closed.",
    "person.due": "📅 Due ({currency}): {date}",
    "person.history": "History:",
    "debt.hist.borrowed": "📥 Borrowed {amount}",
    "debt.hist.lent": "📤 Lent {amount}",
    "debt.hist.repaid_by_me": "💸 You repaid {amount}",
    "debt.hist.repaid_to_me": "✅ They repaid {amount}",
    "debt.btn.due": "📅 Due date",
    "debt.btn.close": "✅ Close debt",
    "debt.btn.delete": "🗑 Delete person",
    "debt.btn.close_yes": "✅ Yes, close",
    "debt.btn.delete_yes": "🗑 Yes, delete",
    "btn.back": "⬅️ Back",
    "debt.close.confirm": "Close the debt with {person}? The remaining <b>{amount}</b> will be marked as repaid.",
    "debt.close.done": "✅ Debt with {person} is closed ({amount} marked as repaid).",
    "debt.close.note": "closed manually",
    "debt.delete.confirm": "Delete <b>{person}</b> and all their debt history? This cannot be undone.",
    "debt.delete.done": "🗑 {person} deleted.",
    "debt.nothing": "Nothing to do here: this debt is already closed.",
    # --- Phase 5: reports, history, categories ---
    "report.week": "📊 <b>This week</b>: {start} – {end}",
    "report.month": "📊 <b>This month</b>: {start} – {end}",
    "report.empty": "No records for this period yet.",
    "report.spent": "💸 Spent: <b>{total}</b>",
    "report.income": "💰 Income: <b>{total}</b>",
    "report.others": "… other categories ({count})",
    "history.title": "🕘 <b>Last records</b>",
    "history.empty": "No records yet. Send an amount to add one.",
    "history.hint": "Tap 🗑 with a number to delete that record.",
    "history.deleted": "🗑 Deleted",
    "categories.title": "🗂 <b>Categories</b>",
    "categories.expense": "💸 <b>Expenses:</b> {names}",
    "categories.income": "💰 <b>Income:</b> {names}",
    "categories.hint": (
        "Your own categories are the buttons below: tap one to rename or remove it. "
        "Built-in categories can't be changed."
    ),
    "categories.none": "You have no categories of your own yet.",
    "category.btn.add_expense": "➕ Expense category",
    "category.btn.add_income": "➕ Income category",
    "category.btn.rename": "✏️ Rename",
    "category.btn.remove": "🗑 Remove",
    "category.btn.delete_yes": "🗑 Yes, delete",
    "category.btn.hide_yes": "🙈 Yes, hide",
    "category.type.expense": "Expense",
    "category.type.income": "Income",
    "category.menu": "{emoji} <b>{name}</b> · {type}\nRecords: {count}",
    "category.ask_name.expense": (
        "✍️ Send the name of the new expense category. "
        "You can start with an emoji, for example: <code>🐶 Pets</code>"
    ),
    "category.ask_name.income": (
        "✍️ Send the name of the new income category. "
        "You can start with an emoji, for example: <code>🎓 Scholarship</code>"
    ),
    "category.ask_rename": "✍️ Send the new name for {emoji} {name}. You can start with an emoji.",
    "category.name_invalid": "Please send a name of 1 to 30 characters, for example: <code>🐶 Pets</code>",
    "category.exists": "A category with this name already exists.",
    "category.limit": "You already have {limit} categories of this type.",
    "category.added": "✅ Category added: {emoji} {name}",
    "category.restored": "✅ Category is back: {emoji} {name}",
    "category.renamed": "✅ Renamed to {emoji} {name}",
    "category.remove.confirm_empty": "Delete the category {emoji} <b>{name}</b>? It has no records.",
    "category.remove.confirm_used": (
        "{emoji} <b>{name}</b> has {count} records. "
        "It will be hidden from the buttons, and the records stay. Hide it?"
    ),
    "category.removed": "🗑 Category deleted: {emoji} {name}",
    "category.hidden": (
        "🙈 Category hidden: {emoji} {name}. Its {count} records are kept. "
        "Add a category with the same name to bring it back."
    ),
    "category.gone": "This category no longer exists.",
    # --- Phase 6: budgets, settings, reminders, export ---
    "budget.title": "💰 <b>Budgets</b> · {start} – {end}",
    "budget.line": "{emoji} {name}: {spent} of {limit} ({percent}%)",
    "budget.empty": (
        "No budgets yet. A budget is a monthly limit for one category. "
        "I'll warn you at 80% and at 100%."
    ),
    "budget.hint": "Tap a budget to change it, or add a new one.",
    "budget.btn.add": "➕ Set a limit",
    "budget.btn.change": "✏️ Change limit",
    "budget.btn.remove": "🗑 Remove",
    "budget.pick_category": "Choose the category for the monthly limit:",
    "budget.menu": "{emoji} <b>{name}</b>\nLimit: {limit}\nSpent this month: {spent} ({percent}%)",
    "budget.ask_amount": "✍️ Send the monthly limit for {emoji} {name} in {currency}, for example <code>300k</code>:",
    "budget.wrong_currency": "Please send the limit in {currency} (your main currency).",
    "budget.saved": "✅ Limit set: {emoji} {name} — {limit} per month",
    "budget.removed": "🗑 Budget removed: {emoji} {name}",
    "budget.gone": "This budget no longer exists.",
    "budget.alert.warning": "⚠️ {emoji} {name}: {percent}% of the monthly budget used ({spent} of {limit}).",
    "budget.alert.exceeded": "🚨 {emoji} {name}: monthly budget reached ({spent} of {limit}, {percent}%).",
    "settings.title": "⚙️ <b>Settings</b>",
    "settings.language": "🌐 Language: <b>{value}</b>",
    "settings.currency": "💱 Main currency: <b>{value}</b>",
    "settings.evening": "🌙 Evening reminder: <b>{value}</b>",
    "settings.debt": "🔔 Debt reminders: <b>{value}</b>",
    "settings.on": "on",
    "settings.off": "off",
    "settings.btn.language": "🌐 Language",
    "settings.btn.currency": "💱 Currency",
    "settings.btn.evening": "🌙 Evening reminder",
    "settings.btn.debt": "🔔 Debt reminders",
    "settings.btn.off": "Turn off",
    "settings.currency_prompt": (
        "💱 Choose your main currency. It is used when you send an amount without a currency "
        "(and for new budgets)."
    ),
    "settings.evening_prompt": "🌙 When should I remind you to log today's expenses?",
    "settings.evening_other": "✍️ Other time",
    "settings.ask_time": "✍️ Send the time as HH:MM, for example <code>21:30</code>:",
    "settings.time_invalid": "I couldn't read that time. Please use HH:MM, for example <code>21:30</code>.",
    "settings.saved": "✅ Saved",
    "reminder.tomorrow.i_owe": "⏰ Tomorrow you should return {amount} to {person}.",
    "reminder.tomorrow.they_owe": "⏰ Tomorrow {person} should return {amount} to you.",
    "reminder.today.i_owe": "⏰ Today you should return {amount} to {person}.",
    "reminder.today.they_owe": "⏰ Today {person} should return {amount} to you.",
    "reminder.overdue.i_owe": "🕓 Overdue since {date}: you owe {person} {amount}.",
    "reminder.overdue.they_owe": "🕓 Overdue since {date}: {person} owes you {amount}.",
    "reminder.btn.repaid": "✅ Repaid",
    "reminder.btn.postpone": "⏰ Postpone",
    "reminder.postponed": "⏰ OK, I'll remind you again in {days} days.",
    "reminder.evening": (
        "🌙 Evening check-in: have you logged all of today's expenses?\n"
        "Send an amount, for example <code>10000 bread</code>."
    ),
    "reminder.evening_total": "Spent today: <b>{total}</b>",
    "reminder.test_done": "🧪 Test finished. Debt reminders sent: {debts}. Evening reminder: sent.",
    "reminder.test_bad_date": "I couldn't read that date. Send /remindtest or /remindtest DD.MM.YYYY.",
    "export.col.date": "Date",
    "export.col.type": "Type",
    "export.col.category": "Category",
    "export.col.amount": "Amount",
    "export.col.currency": "Currency",
    "export.col.note": "Note",
    "export.col.person": "Person",
    "export.col.kind": "Kind",
    "export.col.balance_change": "Balance change (+ owed to me, - I owe)",
    "export.col.due": "Due date",
    "export.kind.borrowed": "Borrowed",
    "export.kind.lent": "Lent",
    "export.kind.repaid_by_me": "Repaid by me",
    "export.kind.repaid_to_me": "Repaid to me",
    "export.empty": "Nothing to export yet.",
    "export.caption.transactions": "📤 Income and expenses",
    "export.caption.debts": "📤 Debts (separate file)",
    # --- Phase 7: hardening ---
    "error.generic": "😕 Something went wrong. Please try again in a moment. Your saved data is safe.",
    "msg.only_text": "📝 I understand text messages. Send an amount, for example <code>10000 bread</code>.",
    "msg.too_long": "📏 That message is too long. Please send a short note (up to 1000 characters).",
    "throttle.slow_down": "⏳ Too fast! Please wait a few seconds.",
    "menu.start": "Start / Guide",
    "menu.today": "Today",
    "menu.week": "This week",
    "menu.month": "This month",
    "menu.history": "Last records",
    "menu.undo": "Undo last record",
    "menu.debts": "Debts",
    "menu.categories": "Categories",
    "menu.budget": "Budgets",
    "menu.export": "Export CSV",
    "menu.settings": "Settings",
    "menu.language": "Language",
}
