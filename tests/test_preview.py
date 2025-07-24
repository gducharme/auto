from datetime import datetime, timezone

import types
import pytest
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

    create_preview(
        session, "p1", "mastodon", template_path=str(template), use_llm=False
    )

    first = session.get(PostPreview, {"post_id": "p1", "network": "mastodon"})
    assert first is not None
    template.write_text("Updated:\n{{ content }}")
    create_preview(
        session, "p1", "mastodon", template_path=str(template), use_llm=False
    )

    second = session.get(PostPreview, {"post_id": "p1", "network": "mastodon"})
    assert second is not None
    assert session.query(PostPreview).count() == 1


def test_create_preview_validates_json(session, tmp_path, monkeypatch):
    post = Post(
        id="p2",
        title="Title",
        link="http://example",
        content="Content",
        summary="",
        published="",
    )
    status = PostStatus(
        post_id="p2", network="mastodon", scheduled_at=datetime.now(timezone.utc)
    )
    session.add_all([post, status])
    session.commit()

    template = tmp_path / "tmpl.txt"
    template.write_text("text")

    class DummyLM:
        def __call__(self, *args, **kwargs):
            return ["not json"]

    dummy = types.SimpleNamespace(
        LM=lambda *a, **k: DummyLM(), configure=lambda *a, **k: None
    )
    monkeypatch.setattr("auto.preview.dspy", dummy)

    with pytest.raises(ValueError):
        create_preview(
            session, "p2", "mastodon", template_path=str(template), use_llm=True
        )

    assert session.get(PostPreview, {"post_id": "p2", "network": "mastodon"}) is None
