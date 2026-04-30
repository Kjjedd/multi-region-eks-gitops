from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    author: str = Field(min_length=1, max_length=50)


class PostCreate(PostBase):
    pass


class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    author: str | None = Field(default=None, min_length=1, max_length=50)


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class PostListResponse(BaseModel):
    items: list[PostResponse]
    page: int
    page_size: int
    total: int
