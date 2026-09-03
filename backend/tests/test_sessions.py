from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.cli import create_user
from app.db import SessionLocal, engine
from app.models import Base, PromptTemplate
from app.seed import seed


@pytest.fixture(autouse=True)
async def _schema():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def _logged_in_client(client, email: str, password: str = "hunter22-secret"):
    await create_user(email, password)
    await client.post("/auth/login", json={"email": email, "password": password})
    return client


async def test_seed_creates_exactly_four_system_templates():
    await seed()
    async with SessionLocal() as db:
        from sqlalchemy import select

        result = await db.execute(select(PromptTemplate).where(PromptTemplate.is_system.is_(True)))
        templates = result.scalars().all()
    assert len(templates) == 4


async def test_create_session_and_it_appears_in_list(client):
    await seed()
    await _logged_in_client(client, "betreiber@example.com")

    templates = await client.get("/prompt-templates")
    format_id = templates.json()[0]["id"]

    created = await client.post("/sessions", json={"format_id": format_id})
    assert created.status_code == 201

    listed = await client.get("/sessions")
    assert listed.status_code == 200
    ids = [s["id"] for s in listed.json()]
    assert created.json()["id"] in ids


async def test_create_session_unknown_format_rejected(client):
    await _logged_in_client(client, "betreiber@example.com")

    resp = await client.post("/sessions", json={"format_id": "00000000-0000-0000-0000-000000000000"})
    assert resp.status_code == 404


async def test_second_user_does_not_see_first_users_session(client):
    await seed()
    await _logged_in_client(client, "first@example.com")
    templates = await client.get("/prompt-templates")
    format_id = templates.json()[0]["id"]
    await client.post("/sessions", json={"format_id": format_id})

    await client.post("/auth/logout")
    await _logged_in_client(client, "second@example.com")

    listed = await client.get("/sessions")
    assert listed.json() == []


async def test_session_survives_new_db_session_scope(client):
    """Simulates a backend restart: a fresh AsyncSession against the same DB still sees it."""
    await seed()
    await _logged_in_client(client, "betreiber@example.com")
    templates = await client.get("/prompt-templates")
    format_id = templates.json()[0]["id"]
    created = await client.post("/sessions", json={"format_id": format_id})

    from sqlalchemy import select

    from app.models import Session as SessionModel

    async with SessionLocal() as fresh_db:
        result = await fresh_db.execute(
            select(SessionModel).where(SessionModel.id == created.json()["id"])
        )
        assert result.scalar_one_or_none() is not None
