from __future__ import annotations

import os

import asyncpg
import pytest

TEST_DB_NAME = "grillme_test"
ADMIN_URL = os.environ.get(
    "TEST_DATABASE_ADMIN_URL", "postgresql://grillme:change-me@localhost:5432/postgres"
)
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", f"postgresql+asyncpg://grillme:change-me@localhost:5432/{TEST_DB_NAME}"
)

# Tests import app modules that read settings at import time (app.db/app.config) — set before
# any import. SESSION_SECRET has no code default (fail-fast in production), so tests must supply
# one explicitly.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("SESSION_SECRET", "test-session-secret")


@pytest.fixture(scope="session", autouse=True)
async def _test_database():
    """Create a dedicated, disposable test database so tests never touch dev data."""
    admin_dsn = ADMIN_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(admin_dsn)
    try:
        await conn.execute(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}" WITH (FORCE)')
        await conn.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        await conn.close()

    yield

    conn = await asyncpg.connect(admin_dsn)
    try:
        await conn.execute(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}" WITH (FORCE)')
    finally:
        await conn.close()
