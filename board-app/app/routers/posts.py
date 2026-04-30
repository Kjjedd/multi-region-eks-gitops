from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.database import get_session
from app.metrics import POSTS_CREATED_TOTAL, refresh_posts_total
from app.models import Post
from app.templating import templates

router = APIRouter(tags=["posts-web"])


def _ctx(request: Request, settings: Settings, **extra: object) -> dict[str, object]:
    base: dict[str, object] = {
        "region": settings.app_region,
        "env": settings.app_env,
        "version": settings.app_version,
        "pod": request.app.state.hostname,
    }
    base.update(extra)
    return base


@router.get("/", response_class=HTMLResponse)
async def list_view(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    total = await session.scalar(select(func.count()).select_from(Post)) or 0
    stmt = (
        select(Post)
        .order_by(Post.created_at.desc(), Post.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await session.execute(stmt)
    items = result.scalars().all()
    total_pages = max(1, (int(total) + page_size - 1) // page_size)
    return templates.TemplateResponse(
        request,
        "list.html",
        _ctx(
            request,
            settings,
            posts=items,
            page=page,
            page_size=page_size,
            total=int(total),
            total_pages=total_pages,
        ),
    )


@router.get("/posts/new", response_class=HTMLResponse)
async def new_view(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> Response:
    return templates.TemplateResponse(request, "new.html", _ctx(request, settings))


@router.post("/posts")
async def create_view(
    title: str = Form(...),
    content: str = Form(...),
    author: str = Form(...),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    post = Post(title=title.strip(), content=content, author=author.strip())
    session.add(post)
    await session.commit()
    await session.refresh(post)
    POSTS_CREATED_TOTAL.inc()
    await refresh_posts_total(session)
    return RedirectResponse(url=f"/posts/{post.id}", status_code=303)


@router.get("/posts/{post_id}", response_class=HTMLResponse)
async def detail_view(
    post_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    post = await session.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")
    return templates.TemplateResponse(request, "detail.html", _ctx(request, settings, post=post))


@router.get("/posts/{post_id}/edit", response_class=HTMLResponse)
async def edit_view(
    post_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    post = await session.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")
    return templates.TemplateResponse(request, "edit.html", _ctx(request, settings, post=post))


@router.post("/posts/{post_id}/edit")
async def update_view(
    post_id: int,
    title: str = Form(...),
    content: str = Form(...),
    author: str = Form(...),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    post = await session.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")
    post.title = title.strip()
    post.content = content
    post.author = author.strip()
    await session.commit()
    return RedirectResponse(url=f"/posts/{post_id}", status_code=303)


@router.post("/posts/{post_id}/delete")
async def delete_view(
    post_id: int,
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    post = await session.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")
    await session.delete(post)
    await session.commit()
    await refresh_posts_total(session)
    return RedirectResponse(url="/", status_code=303)
