"""/categories: add, rename and remove your own categories."""
import html

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.categories import MAX_CUSTOM_PER_TYPE
from app.db.models import User
from app.handlers.debt_views import edit_or_send, message_ref
from app.handlers.utils import safe_edit
from app.i18n import t
from app.keyboards.debt import cancel_keyboard
from app.keyboards.manage import (
    CatAddCb,
    CatListCb,
    CatMenuCb,
    CatRemoveCb,
    CatRemoveOkCb,
    CatRenameCb,
    back_to_categories_keyboard,
    categories_keyboard,
    category_menu_keyboard,
    remove_confirm_keyboard,
)
from app.services.categories import (
    AddStatus,
    RemoveStatus,
    RenameStatus,
    add_category,
    category_name,
    count_records,
    get_own_category,
    list_categories,
    remove_category,
    rename_category,
)
from app.services.pending import Pending, PendingState, consume_pending, create_pending

router = Router(name="categories")

ESC = html.escape


async def overview_screen(session: AsyncSession, user: User) -> tuple[str, InlineKeyboardMarkup]:
    lang = user.language
    expense = await list_categories(session, user.id, "expense")
    income = await list_categories(session, user.id, "income")

    def names(categories) -> str:
        return ", ".join(
            f"{c.emoji} {ESC(category_name(lang, c.name_key, c.name))}" for c in categories
        ) or "\u2014"

    own = [c for c in expense + income if c.user_id == user.id]
    lines = [
        t(lang, "categories.title"),
        "",
        t(lang, "categories.expense", names=names(expense)),
        t(lang, "categories.income", names=names(income)),
        "",
        t(lang, "categories.hint" if own else "categories.none"),
    ]
    return "\n".join(lines), categories_keyboard(own, lang)


@router.message(Command("categories"))
async def cmd_categories(message: Message, session: AsyncSession, user: User) -> None:
    text, markup = await overview_screen(session, user)
    await message.answer(text, reply_markup=markup)


async def _show_overview(callback: CallbackQuery, session: AsyncSession, user: User, prefix: str = "") -> None:
    text, markup = await overview_screen(session, user)
    await safe_edit(callback, prefix + text, markup)


@router.callback_query(CatListCb.filter())
async def on_back(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    await _show_overview(callback, session, user)
    await callback.answer()


@router.callback_query(CatMenuCb.filter())
async def on_menu(
    callback: CallbackQuery, callback_data: CatMenuCb, session: AsyncSession, user: User
) -> None:
    lang = user.language
    category = await get_own_category(session, user.id, callback_data.category_id)
    if category is None:
        await callback.answer(t(lang, "category.gone"))
        await _show_overview(callback, session, user)
        return
    text = t(
        lang,
        "category.menu",
        emoji=category.emoji,
        name=ESC(category.name),
        type=t(lang, f"category.type.{category.type}"),
        count=await count_records(session, category.id),
    )
    await safe_edit(callback, text, category_menu_keyboard(category.id, lang))
    await callback.answer()


@router.callback_query(CatAddCb.filter())
async def on_add(
    callback: CallbackQuery, callback_data: CatAddCb, session: AsyncSession, user: User
) -> None:
    if callback_data.entry_type not in ("expense", "income"):
        await callback.answer(t(user.language, "expired"))
        return
    pending = await create_pending(
        session,
        user.id,
        PendingState.CAT_ADD_NAME,
        {"type": callback_data.entry_type, **message_ref(callback)},
    )
    text = t(user.language, f"category.ask_name.{callback_data.entry_type}")
    await safe_edit(callback, text, cancel_keyboard(pending.token, user.language))
    await callback.answer()


@router.callback_query(CatRenameCb.filter())
async def on_rename(
    callback: CallbackQuery, callback_data: CatRenameCb, session: AsyncSession, user: User
) -> None:
    lang = user.language
    category = await get_own_category(session, user.id, callback_data.category_id)
    if category is None:
        await callback.answer(t(lang, "category.gone"))
        await _show_overview(callback, session, user)
        return
    pending = await create_pending(
        session,
        user.id,
        PendingState.CAT_RENAME_NAME,
        {"category_id": category.id, **message_ref(callback)},
    )
    text = t(lang, "category.ask_rename", emoji=category.emoji, name=ESC(category.name))
    await safe_edit(callback, text, cancel_keyboard(pending.token, lang))
    await callback.answer()


@router.callback_query(CatRemoveCb.filter())
async def on_remove(
    callback: CallbackQuery, callback_data: CatRemoveCb, session: AsyncSession, user: User
) -> None:
    lang = user.language
    category = await get_own_category(session, user.id, callback_data.category_id)
    if category is None:
        await callback.answer(t(lang, "category.gone"))
        await _show_overview(callback, session, user)
        return
    records = await count_records(session, category.id)
    key = "category.remove.confirm_used" if records else "category.remove.confirm_empty"
    text = t(lang, key, emoji=category.emoji, name=ESC(category.name), count=records)
    await safe_edit(callback, text, remove_confirm_keyboard(category.id, records > 0, lang))
    await callback.answer()


@router.callback_query(CatRemoveOkCb.filter())
async def on_remove_confirmed(
    callback: CallbackQuery, callback_data: CatRemoveOkCb, session: AsyncSession, user: User
) -> None:
    lang = user.language
    outcome = await remove_category(session, user.id, callback_data.category_id)
    if outcome.status is RemoveStatus.GONE:
        await callback.answer(t(lang, "category.gone"))
        await _show_overview(callback, session, user)
        return
    key = "category.removed" if outcome.status is RemoveStatus.DELETED else "category.hidden"
    text = t(lang, key, emoji=outcome.emoji, name=ESC(outcome.name), count=outcome.records)
    await safe_edit(callback, text, back_to_categories_keyboard(lang))
    await callback.answer()


# -------------------------------------------------------------- typed text
async def handle_category_text(
    message: Message, session: AsyncSession, user: User, pending: Pending
) -> None:
    """The user typed the name of a new category, or a new name for an existing one."""
    lang = user.language
    ref, text = pending.payload, message.text or ""

    async def done(result_text: str) -> None:
        await consume_pending(session, user.id, pending.token)
        screen, markup = await overview_screen(session, user)
        await edit_or_send(message, ref, f"{result_text}\n\n{screen}", markup)

    if pending.state is PendingState.CAT_ADD_NAME:
        status, category = await add_category(session, user.id, ref["type"], text)
        if status in (AddStatus.ADDED, AddStatus.RESTORED):
            key = "category.added" if status is AddStatus.ADDED else "category.restored"
            await done(t(lang, key, emoji=category.emoji, name=ESC(category.name)))
        elif status is AddStatus.EXISTS:
            await message.answer(t(lang, "category.exists"))
        elif status is AddStatus.LIMIT:
            await message.answer(t(lang, "category.limit", limit=MAX_CUSTOM_PER_TYPE))
        else:
            await message.answer(t(lang, "category.name_invalid"))
        return

    status, category = await rename_category(session, user.id, ref["category_id"], text)
    if status is RenameStatus.RENAMED:
        await done(t(lang, "category.renamed", emoji=category.emoji, name=ESC(category.name)))
    elif status is RenameStatus.GONE:
        await done(t(lang, "category.gone"))
    elif status is RenameStatus.EXISTS:
        await message.answer(t(lang, "category.exists"))
    else:
        await message.answer(t(lang, "category.name_invalid"))
