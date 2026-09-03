from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.cli import create_user
from app.db import engine
from app.models import Base


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


async def test_cli_created_user_can_login(client):
    await create_user("betreiber@example.com", "hunter22-secret")

    resp = await client.post(
        "/auth/login", json={"email": "betreiber@example.com", "password": "hunter22-secret"}
    )
    assert resp.status_code == 200
    assert "session" in resp.cookies


async def test_wrong_password_rejected(client):
    await create_user("betreiber@example.com", "hunter22-secret")

    resp = await client.post(
        "/auth/login", json={"email": "betreiber@example.com", "password": "wrong"}
    )
    assert resp.status_code == 401


async def test_protected_endpoint_without_cookie_rejected(client):
    resp = await client.get("/sessions")
    assert resp.status_code == 401


async def test_protected_endpoint_with_valid_cookie_allowed(client):
    await create_user("betreiber@example.com", "hunter22-secret")
    await client.post(
        "/auth/login", json={"email": "betreiber@example.com", "password": "hunter22-secret"}
    )

    resp = await client.get("/sessions")
    assert resp.status_code == 200
