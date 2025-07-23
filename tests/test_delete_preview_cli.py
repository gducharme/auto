from datetime import datetime, timezone

from auto.cli import publish as tasks
from auto.db import SessionLocal
from auto.models import Post, PostStatus, PostPreview


def test_delete_preview_removes_entry(test_db_engine):
    with SessionLocal() as session:
        post = Post(id="1", title="T", link="http://ex", summary="", published="")
        status = PostStatus(
            post_id="1", network="mastodon", scheduled_at=datetime.now(timezone.utc)
        )
        preview = PostPreview(post_id="1", network="mastodon", content="text")
        session.add_all([post, status, preview])
        session.commit()

    tasks.delete_preview(post_id="1", network="mastodon")

    with SessionLocal() as session:
        result = session.get(PostPreview, {"post_id": "1", "network": "mastodon"})
        assert result is None
