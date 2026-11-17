STRINGS = {
    "start.guide": (
        "👋 Salom! Men xarajat, daromad va qarzlaringizni hisobga olishda yordam beraman.\n\n"
        "Summani yuboring, so'ng kategoriyani tanlang:\n"
        "• <code>10000 non</code>\n"
        "• <code>10k</code>\n"
        "• <code>1.5 mln</code>\n"
        "• <code>50 usd</code>\n\n"
        "Daromad + belgisi bilan boshlanadi: <code>+2000000</code>\n"
        "Qarzlar: summani yuboring, so'ng 🤝 Qarz tugmasini bosing.\n\n"
        "Buyruqlar:\n"
        "/today, /week, /month — hisobotlar\n"
        "/history, /undo — tarix va bekor qilish\n"
        "/debts — qarzlar\n"
        "/categories, /budget — kategoriyalar va byudjet\n"
        "/export, /settings — eksport va sozlamalar\n"
        "/language — tilni o'zgartirish"
    ),
    "lang.hint": "🌐 Til:",
    "lang.choose": "🌐 Tilni tanlang:",
    "lang.changed": "✅ Til: {name}",
    "access.denied": "⛔ Kechirasiz, bu bot shaxsiy.",
    "cat.food": "Oziq-ovqat",
    "cat.transport": "Transport",
    "cat.home": "Uy",
    "cat.health": "Salomatlik",
    "cat.clothes": "Kiyim",
    "cat.fun": "Ko'ngilochar",
    "cat.phone_internet": "Telefon/Internet",
    "cat.other": "Boshqa",
    "cat.salary": "Oylik",
    "cat.gift": "Sovg'a",
    "cat.other_income": "Boshqa daromad",
    # --- Phase 3: expense / income flow ---
    "amount.help": (
        "🤔 Xabarda summa topilmadi.\n\n"
        "Masalan, shunday yuboring:\n"
        "• <code>10000</code>\n"
        "• <code>10k non</code>\n"
        "• <code>+2000000 oylik</code>\n"
        "• <code>50 usd</code>"
    ),
    "amount.zero": "Summa noldan katta bo'lishi kerak. Masalan: <code>10000</code>",
    "amount.decimals": (
        "🔢 O'nli kasr xonalari juda ko'p. UZS da yo'q, USD, EUR va RUB da 2 tagacha. "
        "Sonni tekshiring."
    ),
    "amount.too_large": "🔢 Summa juda katta. Kichikroq summa yuboring.",
    "multi.ask": "🔢 Bir nechta summa topildi. Qaysi birini ishlatay?",
    "large.confirm": "⚠️ Juda katta summa: <b>{amount}</b>. To'g'rimi?",
    "pending.expense": "💸 <b>{amount}</b>{note}\nKategoriyani tanlang:",
    "pending.income": "💰 <b>+{amount}</b>{note}\nKategoriyani tanlang:",
    "btn.cancel": "❌ Bekor qilish",
    "btn.undo": "↩️ Qaytarish",
    "btn.large_ok": "✅ Ha, to'g'ri",
    "saved.expense": "✅ {amount} — {category}{note}. Bugun sarflandi: {total}",
    "saved.income": "✅ +{amount} — {category}{note}. Bugungi daromad: {total}",
    "undo.done": "↩️ Bekor qilindi: {summary}",
    "undo.nothing": "Bekor qilish uchun hech narsa yo'q.",
    "undo.already": "Allaqachon bekor qilingan.",
    "expired": "⌛ Allaqachon ishlatilgan yoki eskirgan. Summani qayta yuboring.",
    "cancelled": "❌ Bekor qilindi.",
    "today.title": "📅 <b>Bugun, {date}</b>",
    "today.empty": "Bugun hali yozuv yo'q. Qo'shish uchun summani yuboring.",
    "today.spent": "Sarflandi: <b>{total}</b>",
    "today.income": "Daromad: <b>{total}</b>",
    "today.more": "…va yana {count} ta avvalgi",
    "cmd.soon": "🚧 Bu buyruq tez orada qo'shiladi.",
    # --- Phase 4: debts ---
    "debt.btn": "🤝 Qarz",
    "debt.kind.borrowed": "📥 Qarz oldim",
    "debt.kind.lent": "📤 Qarz berdim",
    "debt.kind.repaid_by_me": "💸 Qaytardim",
    "debt.kind.repaid_to_me": "✅ Menga qaytarishdi",
    "debt.kind.prompt": "🤝 <b>{amount}</b>{note}\nNima bo'ldi?",
    "debt.person.prompt": "{kind} · <b>{amount}</b>\n👤 Odamni tanlang:",
    "debt.person.new": "➕ Yangi odam",
    "debt.person.ask_name": "✍️ Odamning ismini yozing:",
    "debt.person.name_invalid": "Ismni matn bilan yuboring (100 belgigacha).",
    "debt.person.gone": "Bu odam endi mavjud emas.",
    "debt.due.prompt": "{kind} · <b>{amount}</b> · 👤 {person}\n📅 Qachon qaytarilishi kerak?",
    "debt.due.none": "Muddatsiz",
    "debt.due.w1": "1 haftadan keyin",
    "debt.due.m1": "1 oydan keyin",
    "debt.due.pick": "Sanani tanlash",
    "debt.due.ask_date": "📅 Sanani KK.OO.YYYY ko'rinishida yuboring, masalan <code>{example}</code>:",
    "debt.due.invalid": "Sanani o'qiy olmadim. KK.OO.YYYY ko'rinishida yozing, masalan <code>{example}</code>.",
    "debt.due.past": "Bu sana o'tib ketgan. Bugungi yoki keyingi sanani yuboring.",
    "debt.due.change_prompt": "📅 {person} ({currency}) uchun yangi muddat:",
    "debt.due.changed": "📅 {person} ({currency}) muddati: {date}",
    "debt.due.removed": "📅 {person} ({currency}) muddati olib tashlandi.",
    "debt.entry.borrowed": "📥 {person}dan {amount} qarz oldim",
    "debt.entry.lent": "📤 {person}ga {amount} qarz berdim",
    "debt.entry.repaid_by_me": "💸 {person}ga {amount} qaytardim",
    "debt.entry.repaid_to_me": "✅ {person} {amount} qaytardi",
    "debt.total.you_owe": "Siz {person}ga jami qarzdorsiz: <b>{total}</b>",
    "debt.total.they_owe": "{person} sizga jami qarzdor: <b>{total}</b>",
    "debt.total.closed": "✅ {person} bilan qarz yopildi.",
    "debt.due_line": "📅 Muddat: {date}",
    "debt.warn.no_debt_by_me": (
        "⚠️ Siz {person}ga {currency}da qarzdor emassiz. "
        "{amount}ni unga qarz berganingiz sifatida yozaymi?"
    ),
    "debt.warn.no_debt_to_me": (
        "⚠️ {person} sizga {currency}da qarzdor emas. "
        "{amount}ni undan qarz olganingiz sifatida yozaymi?"
    ),
    "debt.warn.over_by_me": (
        "⚠️ Siz {person}ga faqat {owed} qarzdorsiz, lekin {amount} qaytaryapsiz. "
        "Baribir yozaymi? Shunda {person} sizga {rest} qarzdor bo'ladi."
    ),
    "debt.warn.over_to_me": (
        "⚠️ {person} sizga faqat {owed} qarzdor, lekin {amount} qaytardi. "
        "Baribir yozaymi? Shunda siz {person}ga {rest} qarzdor bo'lasiz."
    ),
    "debt.btn.as_debt": "✅ Ha, qarz sifatida yozish",
    "debt.btn.anyway": "✅ Baribir yozish",
    "debt.repay.prompt_by_me": (
        "💸 {person}ga qancha qaytardingiz? Qarzingiz: <b>{owed}</b>\n"
        "Summani yuboring (masalan <code>100k</code>) yoki to'liq summani bosing."
    ),
    "debt.repay.prompt_to_me": (
        "✅ {person} qancha qaytardi? Uning qarzi: <b>{owed}</b>\n"
        "Summani yuboring (masalan <code>100k</code>) yoki to'liq summani bosing."
    ),
    "debt.repay.full": "To'liq: {amount}",
    "debt.repay.wrong_currency": "Summani {currency}da yuboring.",
    "debts.title": "🤝 <b>Qarzlar</b>",
    "debts.owe_header": "<b>Siz qarzdorsiz:</b>",
    "debts.owed_header": "<b>Sizga qarzdor:</b>",
    "debts.empty": "Faol qarzlar yo'q. Qarz qo'shish uchun summani yuboring va 🤝 Qarz tugmasini bosing.",
    "debts.net.pos": "Jami: sizga qarzdor <b>{total}</b>",
    "debts.net.neg": "Jami: siz qarzdorsiz <b>{total}</b>",
    "debts.net.zero": "Jami: <b>{total}</b>",
    "debts.tap": "Batafsil ko'rish uchun odamni bosing:",
    "person.title": "👤 <b>{person}</b>",
    "person.bal.you_owe": "Siz qarzdorsiz: <b>{total}</b>",
    "person.bal.they_owe": "Sizga qarzdor: <b>{total}</b>",
    "person.closed": "✅ Bu odam bilan barcha qarzlar yopilgan.",
    "person.due": "📅 Muddat ({currency}): {date}",
    "person.history": "Tarix:",
    "debt.hist.borrowed": "📥 Qarz oldingiz {amount}",
    "debt.hist.lent": "📤 Qarz berdingiz {amount}",
    "debt.hist.repaid_by_me": "💸 Siz qaytardingiz {amount}",
    "debt.hist.repaid_to_me": "✅ Sizga qaytarishdi {amount}",
    "debt.btn.due": "📅 Muddat",
    "debt.btn.close": "✅ Qarzni yopish",
    "debt.btn.delete": "🗑 Odamni o'chirish",
    "debt.btn.close_yes": "✅ Ha, yopish",
    "debt.btn.delete_yes": "🗑 Ha, o'chirish",
    "btn.back": "⬅️ Orqaga",
    "debt.close.confirm": "{person} bilan qarzni yopaymi? Qolgan <b>{amount}</b> qaytarilgan deb belgilanadi.",
    "debt.close.done": "✅ {person} bilan qarz yopildi ({amount} qaytarilgan deb belgilandi).",
    "debt.close.note": "qo'lda yopildi",
    "debt.delete.confirm": "<b>{person}</b> va uning barcha qarz tarixini o'chiraymi? Buni qaytarib bo'lmaydi.",
    "debt.delete.done": "🗑 {person} o'chirildi.",
    "debt.nothing": "Bu yerda qiladigan ish yo'q: qarz allaqachon yopilgan.",
    # --- Phase 5: reports, history, categories ---
    "report.week": "📊 <b>Shu hafta</b>: {start} – {end}",
    "report.month": "📊 <b>Shu oy</b>: {start} – {end}",
    "report.empty": "Bu davr uchun hali yozuv yo'q.",
    "report.spent": "💸 Sarflandi: <b>{total}</b>",
    "report.income": "💰 Daromad: <b>{total}</b>",
    "report.others": "… boshqa kategoriyalar ({count})",
    "history.title": "🕘 <b>So'nggi yozuvlar</b>",
    "history.empty": "Hali yozuv yo'q. Qo'shish uchun summani yuboring.",
    "history.hint": "Yozuvni o'chirish uchun raqamli 🗑 tugmasini bosing.",
    "history.deleted": "🗑 O'chirildi",
    "categories.title": "🗂 <b>Kategoriyalar</b>",
    "categories.expense": "💸 <b>Xarajatlar:</b> {names}",
    "categories.income": "💰 <b>Daromadlar:</b> {names}",
    "categories.hint": (
        "O'zingizning kategoriyalaringiz pastdagi tugmalar: nomini o'zgartirish yoki o'chirish uchun bosing. "
        "Ichki kategoriyalarni o'zgartirib bo'lmaydi."
    ),
    "categories.none": "Hali o'zingizning kategoriyalaringiz yo'q.",
    "category.btn.add_expense": "➕ Xarajat kategoriyasi",
    "category.btn.add_income": "➕ Daromad kategoriyasi",
    "category.btn.rename": "✏️ Nomini o'zgartirish",
    "category.btn.remove": "🗑 O'chirish",
    "category.btn.delete_yes": "🗑 Ha, o'chirish",
    "category.btn.hide_yes": "🙈 Ha, yashirish",
    "category.type.expense": "Xarajat",
    "category.type.income": "Daromad",
    "category.menu": "{emoji} <b>{name}</b> · {type}\nYozuvlar: {count}",
    "category.ask_name.expense": (
        "✍️ Yangi xarajat kategoriyasining nomini yuboring. "
        "Emoji bilan boshlashingiz mumkin, masalan: <code>🐶 Uy hayvonlari</code>"
    ),
    "category.ask_name.income": (
        "✍️ Yangi daromad kategoriyasining nomini yuboring. "
        "Emoji bilan boshlashingiz mumkin, masalan: <code>🎓 Stipendiya</code>"
    ),
    "category.ask_rename": "✍️ {emoji} {name} uchun yangi nom yuboring. Emoji bilan boshlashingiz mumkin.",
    "category.name_invalid": "1 dan 30 gacha belgidan iborat nom yuboring, masalan: <code>🐶 Uy hayvonlari</code>",
    "category.exists": "Bunday nomli kategoriya allaqachon bor.",
    "category.limit": "Bu turdagi kategoriyalaringiz allaqachon {limit} ta.",
    "category.added": "✅ Kategoriya qo'shildi: {emoji} {name}",
    "category.restored": "✅ Kategoriya qaytarildi: {emoji} {name}",
    "category.renamed": "✅ Yangi nom: {emoji} {name}",
    "category.remove.confirm_empty": "{emoji} <b>{name}</b> kategoriyasini o'chiraymi? Unda yozuvlar yo'q.",
    "category.remove.confirm_used": (
        "{emoji} <b>{name}</b> kategoriyasida {count} ta yozuv bor. "
        "U tugmalardan yashiriladi, yozuvlar saqlanadi. Yashiraymi?"
    ),
    "category.removed": "🗑 Kategoriya o'chirildi: {emoji} {name}",
    "category.hidden": (
        "🙈 Kategoriya yashirildi: {emoji} {name}. {count} ta yozuv saqlandi. "
        "Uni qaytarish uchun xuddi shu nomli kategoriya qo'shing."
    ),
    "category.gone": "Bu kategoriya endi mavjud emas.",
    # --- Phase 6: budgets, settings, reminders, export ---
    "budget.title": "💰 <b>Byudjetlar</b> · {start} – {end}",
    "budget.line": "{emoji} {name}: {spent} / {limit} ({percent}%)",
    "budget.empty": (
        "Hali byudjet yo'q. Byudjet — bitta kategoriya uchun oylik limit. "
        "80% va 100% da ogohlantiraman."
    ),
    "budget.hint": "O'zgartirish uchun byudjetni bosing yoki yangisini qo'shing.",
    "budget.btn.add": "➕ Limit belgilash",
    "budget.btn.change": "✏️ Limitni o'zgartirish",
    "budget.btn.remove": "🗑 O'chirish",
    "budget.pick_category": "Oylik limit uchun kategoriyani tanlang:",
    "budget.menu": "{emoji} <b>{name}</b>\nLimit: {limit}\nShu oyda sarflandi: {spent} ({percent}%)",
    "budget.ask_amount": "✍️ {emoji} {name} uchun oylik limitni {currency}da yuboring, masalan <code>300k</code>:",
    "budget.wrong_currency": "Limitni {currency}da yuboring (asosiy valyutangiz).",
    "budget.saved": "✅ Limit belgilandi: {emoji} {name} — oyiga {limit}",
    "budget.removed": "🗑 Byudjet o'chirildi: {emoji} {name}",
    "budget.gone": "Bu byudjet endi mavjud emas.",
    "budget.alert.warning": "⚠️ {emoji} {name}: oylik byudjetning {percent}% ishlatildi ({spent} / {limit}).",
    "budget.alert.exceeded": "🚨 {emoji} {name}: oylik byudjet tugadi ({spent} / {limit}, {percent}%).",
    "settings.title": "⚙️ <b>Sozlamalar</b>",
    "settings.language": "🌐 Til: <b>{value}</b>",
    "settings.currency": "💱 Asosiy valyuta: <b>{value}</b>",
    "settings.evening": "🌙 Kechki eslatma: <b>{value}</b>",
    "settings.debt": "🔔 Qarz eslatmalari: <b>{value}</b>",
    "settings.on": "yoqilgan",
    "settings.off": "o'chirilgan",
    "settings.btn.language": "🌐 Til",
    "settings.btn.currency": "💱 Valyuta",
    "settings.btn.evening": "🌙 Kechki eslatma",
    "settings.btn.debt": "🔔 Qarz eslatmalari",
    "settings.btn.off": "O'chirish",
    "settings.currency_prompt": (
        "💱 Asosiy valyutani tanlang. Valyutasiz summa yuborsangiz shu ishlatiladi "
        "(yangi byudjetlar ham)."
    ),
    "settings.evening_prompt": "🌙 Bugungi xarajatlarni yozishni qachon eslatay?",
    "settings.evening_other": "✍️ Boshqa vaqt",
    "settings.ask_time": "✍️ Vaqtni SS:DD ko'rinishida yuboring, masalan <code>21:30</code>:",
    "settings.time_invalid": "Vaqtni o'qiy olmadim. SS:DD ko'rinishida yozing, masalan <code>21:30</code>.",
    "settings.saved": "✅ Saqlandi",
    "reminder.tomorrow.i_owe": "⏰ Ertaga siz {person}ga {amount} qaytarishingiz kerak.",
    "reminder.tomorrow.they_owe": "⏰ Ertaga {person} sizga {amount} qaytarishi kerak.",
    "reminder.today.i_owe": "⏰ Bugun siz {person}ga {amount} qaytarishingiz kerak.",
    "reminder.today.they_owe": "⏰ Bugun {person} sizga {amount} qaytarishi kerak.",
    "reminder.overdue.i_owe": "🕓 Muddat {date} da o'tgan: siz {person}ga {amount} qarzdorsiz.",
    "reminder.overdue.they_owe": "🕓 Muddat {date} da o'tgan: {person} sizga {amount} qarzdor.",
    "reminder.btn.repaid": "✅ Qaytarildi",
    "reminder.btn.postpone": "⏰ Keyinga qoldirish",
    "reminder.postponed": "⏰ Xo'p, {days} kundan keyin yana eslataman.",
    "reminder.evening": (
        "🌙 Kechki eslatma: bugungi barcha xarajatlarni yozdingizmi?\n"
        "Summani yuboring, masalan <code>10000 non</code>."
    ),
    "reminder.evening_total": "Bugun sarflandi: <b>{total}</b>",
    "reminder.test_done": "🧪 Sinov tugadi. Yuborilgan qarz eslatmalari: {debts}. Kechki eslatma: yuborildi.",
    "reminder.test_bad_date": "Sanani o'qiy olmadim. /remindtest yoki /remindtest KK.OO.YYYY yozing.",
    "export.col.date": "Sana",
    "export.col.type": "Turi",
    "export.col.category": "Kategoriya",
    "export.col.amount": "Summa",
    "export.col.currency": "Valyuta",
    "export.col.note": "Izoh",
    "export.col.person": "Odam",
    "export.col.kind": "Turi",
    "export.col.balance_change": "Balans o'zgarishi (+ menga qarzdor, - men qarzdor)",
    "export.col.due": "Muddat",
    "export.kind.borrowed": "Qarz oldim",
    "export.kind.lent": "Qarz berdim",
    "export.kind.repaid_by_me": "Qaytardim",
    "export.kind.repaid_to_me": "Menga qaytarishdi",
    "export.empty": "Hozircha eksport qilish uchun hech narsa yo'q.",
    "export.caption.transactions": "📤 Daromad va xarajatlar",
    "export.caption.debts": "📤 Qarzlar (alohida fayl)",
    # --- Phase 7: hardening ---
    "error.generic": "😕 Nimadir noto'g'ri ketdi. Birozdan keyin qayta urinib ko'ring. Saqlangan ma'lumotlaringiz xavfsiz.",
    "msg.only_text": "📝 Men matnli xabarlarni tushunaman. Summani yuboring, masalan <code>10000 non</code>.",
    "msg.too_long": "📏 Xabar juda uzun. Qisqa izoh yuboring (1000 belgigacha).",
    "throttle.slow_down": "⏳ Juda tez! Bir necha soniya kuting.",
    "menu.start": "Boshlash / Qo'llanma",
    "menu.today": "Bugun",
    "menu.week": "Shu hafta",
    "menu.month": "Shu oy",
    "menu.history": "So'nggi yozuvlar",
    "menu.undo": "Oxirgi yozuvni bekor qilish",
    "menu.debts": "Qarzlar",
    "menu.categories": "Kategoriyalar",
    "menu.budget": "Byudjetlar",
    "menu.export": "CSV eksport",
    "menu.settings": "Sozlamalar",
    "menu.language": "Til",
}
