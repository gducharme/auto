import asyncio

from auto.db import SessionLocal
from auto.models import Post, PostStatus, Task
from auto.mastodon_sync import handle_sync_mastodon_posts
from auto.socials.mastodon_client import MastodonClient


async def run(task, session):
    await handle_sync_mastodon_posts(task, session)


def test_sync_marks_published(monkeypatch, test_db_engine):
    async def fake_fetch_all_statuses(self):
        return [
            {"id": "a", "content": "check http://one"},
            {"id": "b", "content": "id:2"},
        ]

    monkeypatch.setattr(MastodonClient, "fetch_all_statuses", fake_fetch_all_statuses)

    with SessionLocal() as session:
        session.add(
            Post(id="1", title="One", link="http://one", summary="", published="")
        )
        session.add(
            Post(id="2", title="Two", link="http://two", summary="", published="")
        )
        task = Task(type="sync_mastodon_posts")
        session.add(task)
        session.commit()

        asyncio.run(run(task, session))

        ps1 = session.get(PostStatus, {"post_id": "1", "network": "mastodon"})
        ps2 = session.get(PostStatus, {"post_id": "2", "network": "mastodon"})
        assert ps1.status == "published"
        assert ps2.status == "published"


def test_sync_debug_output(monkeypatch, test_db_engine, capsys):
    async def fake_fetch_all_statuses(self):
        return [{"id": "a", "content": "check http://one"}]

    monkeypatch.setattr(MastodonClient, "fetch_all_statuses", fake_fetch_all_statuses)
    monkeypatch.setenv("MASTODON_SYNC_DEBUG", "1")

    with SessionLocal() as session:
        session.add(
            Post(id="1", title="One", link="http://one", summary="", published="")
        )
        task = Task(type="sync_mastodon_posts")
        session.add(task)
        session.commit()

        asyncio.run(run(task, session))

        out = capsys.readouterr().out
        assert "Fetched 1 Mastodon statuses" in out
        assert "STATUS: check http://one" in out
        assert "Post 1 already published" in out
