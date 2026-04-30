from __future__ import annotations

from prometheus_client import Counter, Gauge
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Post

POSTS_TOTAL = Gauge("posts_total", "Current number of posts in the database")
POSTS_CREATED_TOTAL = Counter(
    "posts_created_total", "Cumulative number of posts created since process start"
)


async def refresh_posts_total(session: AsyncSession) -> int:
    total = await session.scalar(select(func.count()).select_from(Post))
    value = int(total or 0)
    POSTS_TOTAL.set(value)
    return value
