from auto.db import SessionLocal
from auto.models import Post
from fastapi.testclient import TestClient
from fastapi import FastAPI
from auto.web_posts import router as posts_router


def test_post_form_insert(test_db_engine, monkeypatch):
    monkeypatch.setenv("SKIP_SLOW_PRINT", "1")
    app = FastAPI()
    app.include_router(posts_router)
    with TestClient(app) as client:
        resp = client.get("/posts/new")
        assert resp.status_code == 200
        assert "<form" in resp.text
        data = {
            "id": "test1",
            "title": "Title",
            "link": "http://example.com",
            "summary": "",
            "published": "",
        }
        resp = client.post("/posts", data=data, follow_redirects=False)
        assert resp.status_code == 303
    with SessionLocal() as session:
        assert session.get(Post, "test1") is not None
