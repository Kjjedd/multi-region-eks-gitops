from __future__ import annotations

import socket
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import select

from app.config import Settings, get_settings
from app.database import (
    Base,
    dispose_engine,
    get_engine,
    get_sessionmaker,
    init_engine,
)
from app.logging_config import configure_logging, get_logger
from app.metrics import refresh_posts_total
from app.middleware import RequestContextMiddleware, ServedByMiddleware
from app.models import Post
from app.routers import ops, posts, posts_api
from app.templating import TEMPLATE_DIR


SAMPLE_POSTS = 5


async def _seed_if_empty() -> None:
    sm = get_sessionmaker()
    async with sm() as session:
        existing = await session.scalar(select(Post.id).limit(1))
        if existing is not None:
            return
        now = datetime.now(timezone.utc).isoformat()
        for i in range(1, SAMPLE_POSTS + 1):
            session.add(
                Post(
                    title=f"샘플 글 {i} — DR 테스트용",
                    content=(
                        "이 글은 백업/복원 검증을 위한 샘플 데이터입니다. "
                        f"작성 시각: {now}"
                    ),
                    author="system",
                )
            )
        await session.commit()
        await refresh_posts_total(session)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings)
    log = get_logger("lifespan")
    init_engine(settings)
    app.state.hostname = socket.gethostname()
    app.state.settings = settings

    engine = get_engine()
    if engine.url.get_backend_name().startswith("sqlite"):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    try:
        await _seed_if_empty()
    except Exception as exc:
        # Seed lazily — DB may not be reachable yet; will retry on next startup.
        log.warning("seed_skipped", reason=str(exc))

    log.info("startup_complete", hostname=app.state.hostname)
    try:
        yield
    finally:
        log.info("shutdown_begin")
        await dispose_engine()
        log.info("shutdown_complete")


def create_app(settings: Settings | None = None) -> FastAPI:
    s = settings or get_settings()
    configure_logging(s)
    app = FastAPI(title="board-app", version=s.app_version, lifespan=lifespan)
    app.state.settings = s
    app.state.hostname = socket.gethostname()

    app.add_middleware(
        ServedByMiddleware,
        region=s.app_region,
        env=s.app_env,
        hostname=app.state.hostname,
    )
    app.add_middleware(RequestContextMiddleware)

    if s.cors_origins_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=s.cors_origins_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    app.include_router(ops.router)
    app.include_router(posts_api.router)
    app.include_router(posts.router)

    static_dir = TEMPLATE_DIR.parent / "static"
    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    return app


app = create_app()
