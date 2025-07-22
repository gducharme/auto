from datetime import datetime, timezone

from auto.preview import create_preview
from auto.models import Post, PostStatus, PostPreview


def test_create_preview_replaces(session, tmp_path):
    post = Post(
        id="p1",
        title="Title",
        link="http://example",
        content="Content",
        summary="",
        published="",
    )
    status = PostStatus(
        post_id="p1", network="mastodon", scheduled_at=datetime.now(timezone.utc)
    )
    session.add_all([post, status])
    session.commit()

    template = tmp_path / "tmpl.txt"
    template.write_text("Summary:\n{{ content }}")

    create_preview(session, "p1", "mastodon", template_path=str(template))

    first = session.get(PostPreview, {"post_id": "p1", "network": "mastodon"})
    assert first is not None
    template.write_text("Updated:\n{{ content }}")
    create_preview(session, "p1", "mastodon", template_path=str(template))

    second = session.get(PostPreview, {"post_id": "p1", "network": "mastodon"})
    assert second is not None
    assert session.query(PostPreview).count() == 1
