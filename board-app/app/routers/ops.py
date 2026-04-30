from __future__ import annotations

import socket

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import Settings, get_settings
from app.database import get_engine

router = APIRouter(tags=["ops"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/ready")
async def ready() -> JSONResponse:
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return JSONResponse(
            status_code=200,
            content={"status": "ready", "checks": {"database": "ok"}},
        )
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not ready",
                "checks": {"database": f"fail: {type(exc).__name__}: {exc}"},
            },
        )


@router.get("/version")
async def version() -> dict[str, str]:
    s: Settings = get_settings()
    return {
        "version": s.app_version,
        "commit": s.app_commit,
        "region": s.app_region,
        "env": s.app_env,
        "hostname": socket.gethostname(),
    }
