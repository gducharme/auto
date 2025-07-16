import sys
from datetime import datetime
from pathlib import Path
from invoke import Context

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import tasks  # noqa: E402
from sqlalchemy import create_engine
from auto.feeds.ingestion import init_db
from auto.db import SessionLocal
from auto.models import Post, PostStatus


def setup_db(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    init_db(str(db_path), engine=engine)
    SessionLocal.configure(bind=engine)
    return engine


def test_quick_post_schedules(monkeypatch, tmp_path):
    setup_db(tmp_path)
    with SessionLocal() as session:
        session.add(
            Post(
                id="1",
                title="One",
                link="http://1",
                summary="",
                published="2000",
                created_at=datetime(2000, 1, 1),
            )
        )
        session.add(
            Post(
                id="2",
                title="Two",
                link="http://2",
                summary="",
                published="1999",
                created_at=datetime(1999, 1, 1),
            )
        )
        session.add(PostStatus(post_id="1", network="mastodon", status="published"))
        session.commit()

    monkeypatch.setattr("builtins.input", lambda prompt='': 'y')

    tasks.quick_post(Context())

    with SessionLocal() as session:
        ps = session.get(PostStatus, {"post_id": "2", "network": "mastodon"})
        assert ps is not None
        assert ps.status == "pending"


def test_quick_post_abort(monkeypatch, tmp_path):
    setup_db(tmp_path)
    with SessionLocal() as session:
        session.add(
            Post(
                id="1",
                title="One",
                link="http://1",
                summary="",
                published="2000",
                created_at=datetime(2000, 1, 1),
            )
        )
        session.commit()

    monkeypatch.setattr("builtins.input", lambda prompt='': 'n')

    tasks.quick_post(Context())

    with SessionLocal() as session:
        statuses = session.query(PostStatus).all()
        assert statuses == []
