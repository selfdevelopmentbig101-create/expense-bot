from app.services.users import get_or_create_user


async def test_creates_user_with_detected_language(session):
    user, created = await get_or_create_user(session, 111, "ru-RU")
    assert created is True
    await session.refresh(user)
    assert user.id is not None
    assert user.language == "ru"
    assert user.currency == "UZS"
    assert user.timezone == "Asia/Tashkent"
    assert user.debt_reminders_enabled is True
    assert user.reminder_time is None
    assert user.created_at.tzinfo is not None


async def test_second_call_returns_same_user(session):
    first, _ = await get_or_create_user(session, 111, "uz")
    second, created = await get_or_create_user(session, 111, "ru")
    assert created is False
    assert second.id == first.id
    assert second.language == "uz"  # language is only guessed on creation


async def test_users_are_separate(session):
    a, _ = await get_or_create_user(session, 1, None)
    b, _ = await get_or_create_user(session, 2, None)
    assert a.id != b.id
    assert a.language == "en"
