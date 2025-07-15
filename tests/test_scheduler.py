import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sqlalchemy import create_engine
from auto.feeds.ingestion import init_db
from auto.db import SessionLocal
from auto.models import Post, PostStatus
from auto.scheduler import process_pending

class DummyPoster:
    called = False

    @classmethod
    def post(cls, text):
        cls.called = True


def test_process_pending_publishes(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    init_db(str(db_path), engine=engine)

    session_factory = SessionLocal
    # override SessionLocal to use this engine
    session_factory.configure(bind=engine)

    with session_factory() as session:
        post = Post(id="1", title="Title", link="http://example", summary="", published="")
        session.add(post)
        status = PostStatus(post_id="1", network="mastodon", scheduled_at=datetime.utcnow() - timedelta(seconds=1))
        session.add(status)
        session.commit()

    monkeypatch.setattr("auto.scheduler.post_to_mastodon", lambda text: DummyPoster.post(text))

    asyncio.run(process_pending())

    with session_factory() as session:
        ps = session.get(PostStatus, {"post_id": "1", "network": "mastodon"})
        assert ps.status == "published"
    assert DummyPoster.called
