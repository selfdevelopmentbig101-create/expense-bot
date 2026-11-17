import pytest_asyncio

from app.db import models  # noqa: F401  (registers tables)
from app.db.base import Base
from app.db.session import create_engine, create_session_factory


@pytest_asyncio.fixture
async def engine(tmp_path):
    """A fresh SQLite file per test, with the same pragmas as production."""
    eng = create_engine(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine):
    factory = create_session_factory(engine)
    async with factory() as s:
        yield s
