from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_healthz_alive(client) -> None:
    r = await client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "alive"}


@pytest.mark.asyncio
async def test_ready_ok_when_db_ok(client) -> None:
    r = await client.get("/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert body["checks"]["database"] == "ok"


@pytest.mark.asyncio
async def test_healthz_alive_even_if_db_dead(client) -> None:
    # Liveness must not depend on DB. Even when SELECT 1 would explode,
    # /healthz returns 200.
    from app.routers import ops

    class DeadEngine:
        def connect(self):  # pragma: no cover - exercised via async_with
            raise RuntimeError("connection refused")

    with patch.object(ops, "get_engine", return_value=DeadEngine()):
        r_health = await client.get("/healthz")
        r_ready = await client.get("/ready")

    assert r_health.status_code == 200
    assert r_ready.status_code == 503
    assert r_ready.json()["status"] == "not ready"
    assert "fail" in r_ready.json()["checks"]["database"]


@pytest.mark.asyncio
async def test_version_payload(client, settings) -> None:
    r = await client.get("/version")
    assert r.status_code == 200
    body = r.json()
    assert body["region"] == settings.app_region
    assert body["env"] == settings.app_env
    assert body["version"] == settings.app_version
    assert body["hostname"]


@pytest.mark.asyncio
async def test_response_headers(client) -> None:
    r = await client.get("/healthz")
    assert r.headers["X-Request-ID"]
    assert float(r.headers["X-Process-Time"]) >= 0
    assert r.headers["X-Served-Region"]
    assert r.headers["X-Served-Env"]
    assert r.headers["X-Served-Pod"]


@pytest.mark.asyncio
async def test_metrics_exposes_prometheus(client) -> None:
    r = await client.get("/metrics")
    assert r.status_code == 200
    assert "posts_total" in r.text
    assert "posts_created_total" in r.text
