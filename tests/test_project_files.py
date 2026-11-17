"""Guards for the things that make a clean setup work, and for secrets."""
import re
from pathlib import Path

from app.i18n import CATALOG, LANGUAGES
from app.logging_setup import _TOKEN_RE
from app.menu import MENU_COMMANDS

ROOT = Path(__file__).resolve().parent.parent


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_dockerfile_runs_as_a_normal_user_with_a_healthcheck_and_migrations():
    text = read("Dockerfile")
    assert "USER bot" in text
    assert "HEALTHCHECK" in text and "app.healthcheck" in text
    assert "alembic upgrade head" in text and "exec python -m app" in text
    assert "COPY migrations" in text and "COPY alembic.ini" in text


def test_compose_keeps_data_in_a_volume_and_restarts_the_bot():
    text = read("docker-compose.yml")
    assert "restart: unless-stopped" in text
    assert "bot-data:/app/data" in text
    assert "env_file: .env" in text


def test_secrets_stay_out_of_git():
    assert re.search(r"^\.env$", read(".gitignore"), re.M)
    assert "*.db" in read(".gitignore")


def test_no_bot_token_is_committed_anywhere():
    checked = 0
    for path in ROOT.rglob("*"):
        if not path.is_file() or "tests" in path.parts or ".git" in path.parts:
            continue
        if path.name != ".env.example" and path.suffix not in {".py", ".md", ".yml", ".yaml", ".txt", ".ini", ".mako"}:
            continue
        checked += 1
        assert not _TOKEN_RE.search(path.read_text(encoding="utf-8", errors="ignore")), path
    assert checked > 20


def test_the_example_env_works_as_a_template():
    text = read(".env.example")
    assert "BOT_TOKEN=put-your-token-from-botfather-here" in text
    assert "ALLOWED_USER_IDS=" in text


def test_every_menu_command_is_translated_and_valid_for_telegram():
    for name in MENU_COMMANDS:
        assert re.fullmatch(r"[a-z0-9_]{1,32}", name)
        for lang in LANGUAGES:
            description = CATALOG[lang][f"menu.{name}"]
            assert 3 <= len(description) <= 256, (lang, name)


def test_the_readme_documents_every_command():
    text = read("README.md")
    for name in MENU_COMMANDS:
        assert f"/{name}" in text, name
    assert "/remindtest" in text
    for step in ("@BotFather", "alembic upgrade head", "docker compose up -d --build", "python -m app.backup"):
        assert step in text, step


def test_requirements_include_everything_the_app_imports():
    text = read("requirements.txt").lower()
    for package in ("aiogram", "sqlalchemy", "aiosqlite", "alembic", "pydantic-settings", "apscheduler", "tzdata"):
        assert package in text, package
