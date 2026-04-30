from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Force SQLite in-memory before any app import.
os.environ.setdefault("DATABASE_URL_OVERRIDE", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("APP_REGION", "test-region")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("APP_VERSION", "0.0.0-test")
os.environ.setdefault("LOG_LEVEL", "WARNING")

from app.config import get_settings  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
def settings():
    get_settings.cache_clear()
    return get_settings()


@pytest_asyncio.fixture
async def client(settings) -> AsyncIterator[AsyncClient]:
    app = create_app(settings)
    transport = ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac
