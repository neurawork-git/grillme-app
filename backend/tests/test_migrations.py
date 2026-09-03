from __future__ import annotations

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import get_settings
from app.models import Base

BACKEND_DIR = Path(__file__).resolve().parent.parent

EXPECTED_TABLES = {
    "user",
    "session",
    "message",
    "decision_node",
    "image",
    "prompt_template",
    "artifact",
    "achievement",
    "token_usage",
}


def _alembic_config() -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return cfg


async def _table_names() -> set[str]:
    engine = create_async_engine(get_settings().database_url)
    async with engine.connect() as conn:
        names = await conn.run_sync(lambda sync_conn: set(inspect(sync_conn).get_table_names()))
    await engine.dispose()
    return names


def test_upgrade_head_creates_all_nine_tables():
    command.upgrade(_alembic_config(), "head")
    try:
        names = asyncio.run(_table_names())
        assert EXPECTED_TABLES <= names
    finally:
        command.downgrade(_alembic_config(), "base")


def test_downgrade_base_removes_all_tables():
    command.upgrade(_alembic_config(), "head")
    command.downgrade(_alembic_config(), "base")

    names = asyncio.run(_table_names())
    assert EXPECTED_TABLES.isdisjoint(names)


# Round trip sanity: metadata declared in models.py matches the migration's table set exactly.
def test_models_metadata_matches_expected_tables():
    assert set(Base.metadata.tables.keys()) == EXPECTED_TABLES
