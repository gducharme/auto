from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .db import SessionLocal
from .models import Post


TEMPLATES = Jinja2Templates(
    directory=str(Path(__file__).resolve().parent / "templates")
)

router = APIRouter()


@router.get("/posts/new", response_class=HTMLResponse)
async def new_post(request: Request) -> HTMLResponse:
    """Render a simple form for creating posts."""
    # Pass the request as the first parameter to avoid deprecation warnings
    # from Starlette's TemplateResponse.
    return TEMPLATES.TemplateResponse(request, "create_post.html")


@router.post("/posts")
async def create_post(
    id: str = Form(...),
    title: str = Form(...),
    link: str = Form(...),
    summary: str = Form(""),
    published: str = Form(""),
) -> RedirectResponse:
    """Save the submitted post data."""
    post = Post(
        id=id,
        title=title,
        link=link,
        summary=summary,
        published=published,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    with SessionLocal() as session:
        session.add(post)
        session.commit()
    return RedirectResponse(url="/posts/new", status_code=303)
