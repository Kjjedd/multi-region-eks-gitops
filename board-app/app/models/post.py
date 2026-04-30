from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

PostId = BigInteger().with_variant(Integer(), "sqlite")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(PostId, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=_utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )

    __table_args__ = (Index("idx_created_at", "created_at"),)
