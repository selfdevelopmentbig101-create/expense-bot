STRINGS = {
    "start.guide": (
        "👋 Привет! Я помогу вести учёт расходов, доходов и долгов.\n\n"
        "Отправьте сумму, затем выберите категорию:\n"
        "• <code>10000 хлеб</code>\n"
        "• <code>10k</code>\n"
        "• <code>1.5 млн</code>\n"
        "• <code>50 usd</code>\n\n"
        "Доход начинается с +: <code>+2000000</code>\n"
        "Долги: отправьте сумму и нажмите 🤝 Долг.\n\n"
        "Команды:\n"
        "/today, /week, /month — отчёты\n"
        "/history, /undo — история и отмена\n"
        "/debts — долги\n"
        "/categories, /budget — категории и бюджет\n"
        "/export, /settings — экспорт и настройки\n"
        "/language — сменить язык"
    ),
    "lang.hint": "🌐 Язык:",
    "lang.choose": "🌐 Выберите язык:",
    "lang.changed": "✅ Язык: {name}",
    "access.denied": "⛔ Извините, этот бот приватный.",
    "cat.food": "Еда",
    "cat.transport": "Транспорт",
    "cat.home": "Дом",
    "cat.health": "Здоровье",
    "cat.clothes": "Одежда",
    "cat.fun": "Развлечения",
    "cat.phone_internet": "Телефон/Интернет",
    "cat.other": "Другое",
    "cat.salary": "Зарплата",
    "cat.gift": "Подарок",
    "cat.other_income": "Другой доход",
    # --- Phase 3: expense / income flow ---
    "amount.help": (
        "🤔 Не нашёл сумму в сообщении.\n\n"
        "Попробуйте, например:\n"
        "• <code>10000</code>\n"
        "• <code>10k хлеб</code>\n"
        "• <code>+2000000 зарплата</code>\n"
        "• <code>50 usd</code>"
    ),
    "amount.zero": "Сумма должна быть больше нуля. Например: <code>10000</code>",
    "amount.decimals": (
        "🔢 Слишком много знаков после запятой. У UZS их нет, у USD, EUR и RUB — 2. "
        "Проверьте число."
    ),
    "amount.too_large": "🔢 Слишком большая сумма. Отправьте меньшую.",
    "multi.ask": "🔢 Нашёл несколько сумм. Какую использовать?",
    "large.confirm": "⚠️ Очень большая сумма: <b>{amount}</b>. Всё верно?",
    "pending.expense": "💸 <b>{amount}</b>{note}\nВыберите категорию:",
    "pending.income": "💰 <b>+{amount}</b>{note}\nВыберите категорию:",
    "btn.cancel": "❌ Отмена",
    "btn.undo": "↩️ Отменить",
    "btn.large_ok": "✅ Да, верно",
    "saved.expense": "✅ {amount} — {category}{note}. Потрачено сегодня: {total}",
    "saved.income": "✅ +{amount} — {category}{note}. Доход за сегодня: {total}",
    "undo.done": "↩️ Отменено: {summary}",
    "undo.nothing": "Нечего отменять.",
    "undo.already": "Уже отменено.",
    "expired": "⌛ Уже использовано или устарело. Отправьте сумму ещё раз.",
    "cancelled": "❌ Отменено.",
    "today.title": "📅 <b>Сегодня, {date}</b>",
    "today.empty": "Сегодня записей пока нет. Отправьте сумму, чтобы добавить.",
    "today.spent": "Потрачено: <b>{total}</b>",
    "today.income": "Доход: <b>{total}</b>",
    "today.more": "…и ещё {count} ранее",
    "cmd.soon": "🚧 Эта команда скоро появится.",
    # --- Phase 4: debts ---
    "debt.btn": "🤝 Долг",
    "debt.kind.borrowed": "📥 Я занял",
    "debt.kind.lent": "📤 Я одолжил",
    "debt.kind.repaid_by_me": "💸 Я вернул",
    "debt.kind.repaid_to_me": "✅ Мне вернули",
    "debt.kind.prompt": "🤝 <b>{amount}</b>{note}\nЧто произошло?",
    "debt.person.prompt": "{kind} · <b>{amount}</b>\n👤 Выберите человека:",
    "debt.person.new": "➕ Новый человек",
    "debt.person.ask_name": "✍️ Напишите имя человека:",
    "debt.person.name_invalid": "Отправьте имя текстом (до 100 символов).",
    "debt.person.gone": "Этого человека больше нет.",
    "debt.due.prompt": "{kind} · <b>{amount}</b> · 👤 {person}\n📅 Когда нужно вернуть?",
    "debt.due.none": "Без срока",
    "debt.due.w1": "Через неделю",
    "debt.due.m1": "Через месяц",
    "debt.due.pick": "Выбрать дату",
    "debt.due.ask_date": "📅 Отправьте дату в формате ДД.ММ.ГГГГ, например <code>{example}</code>:",
    "debt.due.invalid": "Не удалось прочитать дату. Используйте формат ДД.ММ.ГГГГ, например <code>{example}</code>.",
    "debt.due.past": "Эта дата уже прошла. Отправьте сегодняшнюю или более позднюю дату.",
    "debt.due.change_prompt": "📅 Новый срок для {person} ({currency}):",
    "debt.due.changed": "📅 Срок для {person} ({currency}): {date}",
    "debt.due.removed": "📅 Срок для {person} ({currency}) убран.",
    "debt.entry.borrowed": "📥 Я занял {amount} — {person}",
    "debt.entry.lent": "📤 Я одолжил {amount} — {person}",
    "debt.entry.repaid_by_me": "💸 Я вернул {amount} — {person}",
    "debt.entry.repaid_to_me": "✅ Мне вернули {amount} — {person}",
    "debt.total.you_owe": "Вы должны — {person}: <b>{total}</b>",
    "debt.total.they_owe": "Вам должны — {person}: <b>{total}</b>",
    "debt.total.closed": "✅ Долг закрыт — {person}.",
    "debt.due_line": "📅 Срок: {date}",
    "debt.warn.no_debt_by_me": (
        "⚠️ У вас нет долга перед этим человеком ({person}) в {currency}. "
        "Записать {amount} как деньги, которые вы одолжили?"
    ),
    "debt.warn.no_debt_to_me": (
        "⚠️ Этот человек ({person}) ничего вам не должен в {currency}. "
        "Записать {amount} как деньги, которые вы заняли?"
    ),
    "debt.warn.over_by_me": (
        "⚠️ Ваш долг ({person}) — только {owed}, а вы возвращаете {amount}. "
        "Записать всё равно? Тогда этот человек будет должен вам {rest}."
    ),
    "debt.warn.over_to_me": (
        "⚠️ Долг этого человека ({person}) — только {owed}, а вернули {amount}. "
        "Записать всё равно? Тогда вы будете должны ему {rest}."
    ),
    "debt.btn.as_debt": "✅ Да, записать как долг",
    "debt.btn.anyway": "✅ Всё равно записать",
    "debt.repay.prompt_by_me": (
        "💸 Сколько вы вернули ({person})? Ваш долг: <b>{owed}</b>\n"
        "Отправьте сумму (например <code>100k</code>) или нажмите полную."
    ),
    "debt.repay.prompt_to_me": (
        "✅ Сколько вам вернули ({person})? Долг: <b>{owed}</b>\n"
        "Отправьте сумму (например <code>100k</code>) или нажмите полную."
    ),
    "debt.repay.full": "Вся сумма: {amount}",
    "debt.repay.wrong_currency": "Отправьте сумму в {currency}.",
    "debts.title": "🤝 <b>Долги</b>",
    "debts.owe_header": "<b>Вы должны:</b>",
    "debts.owed_header": "<b>Вам должны:</b>",
    "debts.empty": "Активных долгов нет. Отправьте сумму и нажмите 🤝 Долг, чтобы добавить.",
    "debts.net.pos": "Итого: вам должны <b>{total}</b>",
    "debts.net.neg": "Итого: вы должны <b>{total}</b>",
    "debts.net.zero": "Итого: <b>{total}</b>",
    "debts.tap": "Нажмите на человека, чтобы открыть:",
    "person.title": "👤 <b>{person}</b>",
    "person.bal.you_owe": "Вы должны: <b>{total}</b>",
    "person.bal.they_owe": "Вам должны: <b>{total}</b>",
    "person.closed": "✅ Все долги с этим человеком закрыты.",
    "person.due": "📅 Срок ({currency}): {date}",
    "person.history": "История:",
    "debt.hist.borrowed": "📥 Занял {amount}",
    "debt.hist.lent": "📤 Одолжил {amount}",
    "debt.hist.repaid_by_me": "💸 Вы вернули {amount}",
    "debt.hist.repaid_to_me": "✅ Вам вернули {amount}",
    "debt.btn.due": "📅 Срок",
    "debt.btn.close": "✅ Закрыть долг",
    "debt.btn.delete": "🗑 Удалить человека",
    "debt.btn.close_yes": "✅ Да, закрыть",
    "debt.btn.delete_yes": "🗑 Да, удалить",
    "btn.back": "⬅️ Назад",
    "debt.close.confirm": "Закрыть долг ({person})? Остаток <b>{amount}</b> будет отмечен как возвращённый.",
    "debt.close.done": "✅ Долг закрыт — {person} (отмечено как возвращённое: {amount}).",
    "debt.close.note": "закрыто вручную",
    "debt.delete.confirm": "Удалить человека <b>{person}</b> и всю историю долгов? Это нельзя отменить.",
    "debt.delete.done": "🗑 Удалено: {person}.",
    "debt.nothing": "Здесь нечего делать: этот долг уже закрыт.",
    # --- Phase 5: reports, history, categories ---
    "report.week": "📊 <b>Эта неделя</b>: {start} – {end}",
    "report.month": "📊 <b>Этот месяц</b>: {start} – {end}",
    "report.empty": "Записей за этот период пока нет.",
    "report.spent": "💸 Потрачено: <b>{total}</b>",
    "report.income": "💰 Доход: <b>{total}</b>",
    "report.others": "… другие категории ({count})",
    "history.title": "🕘 <b>Последние записи</b>",
    "history.empty": "Записей пока нет. Отправьте сумму, чтобы добавить.",
    "history.hint": "Нажмите 🗑 с номером, чтобы удалить запись.",
    "history.deleted": "🗑 Удалено",
    "categories.title": "🗂 <b>Категории</b>",
    "categories.expense": "💸 <b>Расходы:</b> {names}",
    "categories.income": "💰 <b>Доходы:</b> {names}",
    "categories.hint": (
        "Ваши категории — кнопки ниже: нажмите, чтобы переименовать или удалить. "
        "Встроенные категории изменить нельзя."
    ),
    "categories.none": "Своих категорий пока нет.",
    "category.btn.add_expense": "➕ Категория расходов",
    "category.btn.add_income": "➕ Категория доходов",
    "category.btn.rename": "✏️ Переименовать",
    "category.btn.remove": "🗑 Удалить",
    "category.btn.delete_yes": "🗑 Да, удалить",
    "category.btn.hide_yes": "🙈 Да, скрыть",
    "category.type.expense": "Расход",
    "category.type.income": "Доход",
    "category.menu": "{emoji} <b>{name}</b> · {type}\nЗаписей: {count}",
    "category.ask_name.expense": (
        "✍️ Отправьте название новой категории расходов. "
        "Можно начать с эмодзи, например: <code>🐶 Питомцы</code>"
    ),
    "category.ask_name.income": (
        "✍️ Отправьте название новой категории доходов. "
        "Можно начать с эмодзи, например: <code>🎓 Стипендия</code>"
    ),
    "category.ask_rename": "✍️ Отправьте новое название для {emoji} {name}. Можно начать с эмодзи.",
    "category.name_invalid": "Отправьте название от 1 до 30 символов, например: <code>🐶 Питомцы</code>",
    "category.exists": "Категория с таким названием уже есть.",
    "category.limit": "У вас уже {limit} категорий этого типа.",
    "category.added": "✅ Категория добавлена: {emoji} {name}",
    "category.restored": "✅ Категория снова доступна: {emoji} {name}",
    "category.renamed": "✅ Переименовано: {emoji} {name}",
    "category.remove.confirm_empty": "Удалить категорию {emoji} <b>{name}</b>? В ней нет записей.",
    "category.remove.confirm_used": (
        "В категории {emoji} <b>{name}</b> записей: {count}. "
        "Она будет скрыта из кнопок, записи сохранятся. Скрыть?"
    ),
    "category.removed": "🗑 Категория удалена: {emoji} {name}",
    "category.hidden": (
        "🙈 Категория скрыта: {emoji} {name}. Записи ({count}) сохранены. "
        "Чтобы вернуть её, добавьте категорию с тем же названием."
    ),
    "category.gone": "Этой категории больше нет.",
    # --- Phase 6: budgets, settings, reminders, export ---
    "budget.title": "💰 <b>Бюджеты</b> · {start} – {end}",
    "budget.line": "{emoji} {name}: {spent} из {limit} ({percent}%)",
    "budget.empty": (
        "Бюджетов пока нет. Бюджет — это месячный лимит на одну категорию. "
        "Я предупрежу на 80% и на 100%."
    ),
    "budget.hint": "Нажмите на бюджет, чтобы изменить, или добавьте новый.",
    "budget.btn.add": "➕ Задать лимит",
    "budget.btn.change": "✏️ Изменить лимит",
    "budget.btn.remove": "🗑 Удалить",
    "budget.pick_category": "Выберите категорию для месячного лимита:",
    "budget.menu": "{emoji} <b>{name}</b>\nЛимит: {limit}\nПотрачено в этом месяце: {spent} ({percent}%)",
    "budget.ask_amount": "✍️ Отправьте месячный лимит для {emoji} {name} в {currency}, например <code>300k</code>:",
    "budget.wrong_currency": "Отправьте лимит в {currency} (ваша основная валюта).",
    "budget.saved": "✅ Лимит задан: {emoji} {name} — {limit} в месяц",
    "budget.removed": "🗑 Бюджет удалён: {emoji} {name}",
    "budget.gone": "Этого бюджета больше нет.",
    "budget.alert.warning": "⚠️ {emoji} {name}: использовано {percent}% месячного бюджета ({spent} из {limit}).",
    "budget.alert.exceeded": "🚨 {emoji} {name}: месячный бюджет исчерпан ({spent} из {limit}, {percent}%).",
    "settings.title": "⚙️ <b>Настройки</b>",
    "settings.language": "🌐 Язык: <b>{value}</b>",
    "settings.currency": "💱 Основная валюта: <b>{value}</b>",
    "settings.evening": "🌙 Вечернее напоминание: <b>{value}</b>",
    "settings.debt": "🔔 Напоминания о долгах: <b>{value}</b>",
    "settings.on": "включено",
    "settings.off": "выключено",
    "settings.btn.language": "🌐 Язык",
    "settings.btn.currency": "💱 Валюта",
    "settings.btn.evening": "🌙 Вечернее напоминание",
    "settings.btn.debt": "🔔 Напоминания о долгах",
    "settings.btn.off": "Выключить",
    "settings.currency_prompt": (
        "💱 Выберите основную валюту. Она используется, когда вы отправляете сумму без валюты "
        "(и для новых бюджетов)."
    ),
    "settings.evening_prompt": "🌙 Когда напоминать о записи сегодняшних расходов?",
    "settings.evening_other": "✍️ Другое время",
    "settings.ask_time": "✍️ Отправьте время в формате ЧЧ:ММ, например <code>21:30</code>:",
    "settings.time_invalid": "Не удалось прочитать время. Используйте формат ЧЧ:ММ, например <code>21:30</code>.",
    "settings.saved": "✅ Сохранено",
    "reminder.tomorrow.i_owe": "⏰ Завтра нужно вернуть {amount} — {person}.",
    "reminder.tomorrow.they_owe": "⏰ Завтра {person} должен вернуть вам {amount}.",
    "reminder.today.i_owe": "⏰ Сегодня нужно вернуть {amount} — {person}.",
    "reminder.today.they_owe": "⏰ Сегодня {person} должен вернуть вам {amount}.",
    "reminder.overdue.i_owe": "🕓 Просрочено с {date}: вы должны {amount} — {person}.",
    "reminder.overdue.they_owe": "🕓 Просрочено с {date}: {person} должен вам {amount}.",
    "reminder.btn.repaid": "✅ Возвращено",
    "reminder.btn.postpone": "⏰ Отложить",
    "reminder.postponed": "⏰ Хорошо, напомню снова через {days} дн.",
    "reminder.evening": (
        "🌙 Вечерняя проверка: вы записали все сегодняшние расходы?\n"
        "Отправьте сумму, например <code>10000 хлеб</code>."
    ),
    "reminder.evening_total": "Потрачено сегодня: <b>{total}</b>",
    "reminder.test_done": "🧪 Тест завершён. Отправлено напоминаний о долгах: {debts}. Вечернее напоминание: отправлено.",
    "reminder.test_bad_date": "Не удалось прочитать дату. Напишите /remindtest или /remindtest ДД.ММ.ГГГГ.",
    "export.col.date": "Дата",
    "export.col.type": "Тип",
    "export.col.category": "Категория",
    "export.col.amount": "Сумма",
    "export.col.currency": "Валюта",
    "export.col.note": "Заметка",
    "export.col.person": "Человек",
    "export.col.kind": "Вид",
    "export.col.balance_change": "Изменение баланса (+ должны мне, - я должен)",
    "export.col.due": "Срок",
    "export.kind.borrowed": "Занял",
    "export.kind.lent": "Одолжил",
    "export.kind.repaid_by_me": "Я вернул",
    "export.kind.repaid_to_me": "Мне вернули",
    "export.empty": "Пока нечего экспортировать.",
    "export.caption.transactions": "📤 Доходы и расходы",
    "export.caption.debts": "📤 Долги (отдельный файл)",
    # --- Phase 7: hardening ---
    "error.generic": "😕 Что-то пошло не так. Попробуйте ещё раз чуть позже. Ваши сохранённые данные в безопасности.",
    "msg.only_text": "📝 Я понимаю текстовые сообщения. Отправьте сумму, например <code>10000 хлеб</code>.",
    "msg.too_long": "📏 Слишком длинное сообщение. Отправьте короткую заметку (до 1000 символов).",
    "throttle.slow_down": "⏳ Слишком быстро! Подождите несколько секунд.",
    "menu.start": "Начало / Справка",
    "menu.today": "Сегодня",
    "menu.week": "Эта неделя",
    "menu.month": "Этот месяц",
    "menu.history": "Последние записи",
    "menu.undo": "Отменить последнюю запись",
    "menu.debts": "Долги",
    "menu.categories": "Категории",
    "menu.budget": "Бюджеты",
    "menu.export": "Экспорт CSV",
    "menu.settings": "Настройки",
    "menu.language": "Язык",
}
