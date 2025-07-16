import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auto.db import SessionLocal
from auto.models import Post, PostStatus, PostPreview


def test_updated_at_refreshes(test_db_engine):

    earlier = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)

    with SessionLocal() as session:
        post = Post(
            id="1",
            title="Title",
            link="http://example",
            created_at=earlier,
            updated_at=earlier,
        )
        status = PostStatus(
            post_id="1",
            network="mastodon",
            scheduled_at=datetime.now(timezone.utc).replace(tzinfo=None),
            updated_at=earlier,
        )
        preview = PostPreview(
            post_id="1",
            network="mastodon",
            content="text",
            updated_at=earlier,
        )
        session.add_all([post, status, preview])
        session.commit()

        old_post_ts = post.updated_at
        old_status_ts = status.updated_at
        old_preview_ts = preview.updated_at

        # modify rows
        post.summary = "new"
        status.status = "published"
        preview.content = "newtext"
        session.commit()

        assert post.updated_at > old_post_ts
        assert status.updated_at > old_status_ts
        assert preview.updated_at > old_preview_ts
