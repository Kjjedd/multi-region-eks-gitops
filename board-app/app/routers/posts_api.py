from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.metrics import POSTS_CREATED_TOTAL, refresh_posts_total
from app.models import Post
from app.schemas import PostCreate, PostListResponse, PostResponse, PostUpdate

router = APIRouter(prefix="/api/posts", tags=["posts-api"])


@router.get("", response_model=PostListResponse)
async def list_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> PostListResponse:
    total = await session.scalar(select(func.count()).select_from(Post))
    stmt = (
        select(Post)
        .order_by(Post.created_at.desc(), Post.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    items = result.scalars().all()
    return PostListResponse(
        items=[PostResponse.model_validate(p) for p in items],
        page=page,
        page_size=page_size,
        total=int(total or 0),
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    session: AsyncSession = Depends(get_session),
) -> PostResponse:
    post = await session.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")
    return PostResponse.model_validate(post)


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    payload: PostCreate,
    session: AsyncSession = Depends(get_session),
) -> PostResponse:
    post = Post(title=payload.title, content=payload.content, author=payload.author)
    session.add(post)
    await session.commit()
    await session.refresh(post)
    POSTS_CREATED_TOTAL.inc()
    await refresh_posts_total(session)
    return PostResponse.model_validate(post)


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: int,
    payload: PostUpdate,
    session: AsyncSession = Depends(get_session),
) -> PostResponse:
    post = await session.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(post, k, v)
    await session.commit()
    await session.refresh(post)
    return PostResponse.model_validate(post)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    post = await session.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")
    await session.delete(post)
    await session.commit()
    await refresh_posts_total(session)
