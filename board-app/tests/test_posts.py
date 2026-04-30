from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_seed_data_exists(client) -> None:
    r = await client.get("/api/posts")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 5
    assert any(p["author"] == "system" for p in body["items"])


@pytest.mark.asyncio
async def test_create_get_update_delete_post(client) -> None:
    payload = {"title": "hello", "content": "world", "author": "tester"}
    r = await client.post("/api/posts", json=payload)
    assert r.status_code == 201
    pid = r.json()["id"]

    r = await client.get(f"/api/posts/{pid}")
    assert r.status_code == 200
    assert r.json()["title"] == "hello"

    r = await client.put(f"/api/posts/{pid}", json={"title": "updated"})
    assert r.status_code == 200
    assert r.json()["title"] == "updated"
    assert r.json()["content"] == "world"

    r = await client.delete(f"/api/posts/{pid}")
    assert r.status_code == 204

    r = await client.get(f"/api/posts/{pid}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_validation_error(client) -> None:
    r = await client.post("/api/posts", json={"title": "", "content": "x", "author": "a"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_get_post_not_found(client) -> None:
    r = await client.get("/api/posts/999999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_html_list_renders_with_footer(client) -> None:
    r = await client.get("/")
    assert r.status_code == 200
    assert "게시판" in r.text
    assert "test-region" in r.text


@pytest.mark.asyncio
async def test_html_create_redirects_to_detail(client) -> None:
    r = await client.post(
        "/posts",
        data={"title": "html-title", "content": "html-content", "author": "html-author"},
    )
    assert r.status_code == 303
    assert r.headers["location"].startswith("/posts/")

    detail = await client.get(r.headers["location"])
    assert detail.status_code == 200
    assert "html-title" in detail.text
    assert "html-author" in detail.text
