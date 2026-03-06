import shutil
import json
from pathlib import Path
from datetime import datetime, timezone

from auto.cli import automation as tasks


class DummyController:
    def __init__(self):
        self.calls = []

    def open(self, url):
        self.calls.append(("open", url))
        return "OK"

    def click(self, selector):
        self.calls.append(("click", selector))
        return "OK"

    def fill(self, selector, text):
        self.calls.append(("fill", selector, text))
        return "OK"

    def run_js(self, code):
        self.calls.append(("run_js", code))
        return "OK"

    def close_tab(self):
        self.calls.append(("close_tab",))
        return "OK"


def test_replay_template_variable(monkeypatch, tmp_path):
    src = Path("tests/fixtures/open_var")
    dst = tmp_path / "tests" / "fixtures" / "open_var"
    shutil.copytree(src, dst)
    monkeypatch.chdir(tmp_path)

    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setenv("SKIP_SLOW_PRINT", "1")

    url = "https://example.com/post1"
    inputs = iter(["n"])  # do not continue recording
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    tasks.replay("open_var", post_id=url)

    assert ("open", url) in controller.calls


def test_replay_load_post(monkeypatch, tmp_path, test_db_engine):
    src = Path("tests/fixtures/load_post")
    dst = tmp_path / "tests" / "fixtures" / "load_post"
    shutil.copytree(src, dst)
    monkeypatch.chdir(tmp_path)

    from auto.db import SessionLocal
    from auto.models import Post, PostPreview

    with SessionLocal() as session:
        post = Post(id="1", title="T", link="http://ex", summary="", published="")
        preview = PostPreview(
            post_id="1",
            network="mastodon",
            content='{"tweet": "Hello {{post.title}}"}',
        )
        session.add_all([post, preview])
        session.commit()

    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setenv("SKIP_SLOW_PRINT", "1")

    inputs = iter(["n"])  # do not continue recording
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    tasks.replay("load_post", post_id="1", network="mastodon")

    assert ("open", "Hello T") in controller.calls


def test_replay_mark_published(monkeypatch, tmp_path, test_db_engine):
    src = Path("tests/fixtures/mark_published")
    dst = tmp_path / "tests" / "fixtures" / "mark_published"
    shutil.copytree(src, dst)
    monkeypatch.chdir(tmp_path)

    from auto.db import SessionLocal
    from auto.models import Post, PostPreview, PostStatus

    with SessionLocal() as session:
        post = Post(id="1", title="T", link="http://ex", summary="", published="")
        preview = PostPreview(post_id="1", network="mastodon", content="old")
        status = PostStatus(
            post_id="1", network="mastodon", scheduled_at=datetime.now(timezone.utc)
        )
        session.add_all([post, preview, status])
        session.commit()

    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setenv("SKIP_SLOW_PRINT", "1")

    inputs = iter(["n"])  # do not continue recording
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    tasks.replay("mark_published", post_id="1", network="mastodon")

    with SessionLocal() as session:
        status = session.get(PostStatus, {"post_id": "1", "network": "mastodon"})
        preview = session.get(PostPreview, {"post_id": "1", "network": "mastodon"})
        assert status.status == "published"
        assert preview.content == "Posted text"


def test_replay_load_instagram_pipeline_and_sleep(
    monkeypatch, tmp_path, test_db_engine
):
    fixture_dir = tmp_path / "tests" / "fixtures" / "ig_carousel_demo"
    fixture_dir.mkdir(parents=True)
    (fixture_dir / "commands.json").write_text(
        json.dumps(
            [
                ["load_instagram_pipeline", "{{post_id}}", "instagram", "v1"],
                ["sleep", "0"],
                ["run_js_file", "tests/site_js/instagram.js"],
                ["fill_instagram_caption", "{{instagram_caption}}"],
            ]
        )
    )
    monkeypatch.chdir(tmp_path)

    src_js = Path(__file__).resolve().parent / "site_js" / "instagram.js"
    dst_js = tmp_path / "tests" / "site_js" / "instagram.js"
    dst_js.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src_js, dst_js)

    from auto.db import SessionLocal
    from auto.models import InstagramPipelineRun, Post

    with SessionLocal() as session:
        session.add(
            Post(
                id="ig-1",
                title="Fasting",
                link="http://ex",
                summary="",
                published="",
            )
        )
        session.add(
            InstagramPipelineRun(
                post_id="ig-1",
                network="instagram",
                pipeline_version="v1",
                status="ready",
                publish_payload=json.dumps(
                    {
                        "caption_final": "Line 1\n\nLine 2",
                        "adapter_version": "ig-adapter-v1",
                    }
                ),
            )
        )
        session.commit()

    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setenv("SKIP_SLOW_PRINT", "1")
    inputs = iter(["n"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    tasks.replay("ig_carousel_demo", post_id="ig-1", network="instagram")

    assert any(
        call[0] == "run_js" and "fillCaption(" in call[1] for call in controller.calls
    )


def test_replay_upload_local_instagram_carousel(monkeypatch, tmp_path):
    fixture_dir = tmp_path / "tests" / "fixtures" / "ig_upload_demo"
    fixture_dir.mkdir(parents=True)
    (fixture_dir / "commands.json").write_text(
        json.dumps([["upload_local_instagram_carousel"]])
    )
    monkeypatch.chdir(tmp_path)

    pics_dir = tmp_path / "pics"
    pics_dir.mkdir()
    (pics_dir / "one.jpg").write_text("x")

    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setattr(
        tasks,
        "_upload_local_instagram_carousel_from_pics",
        lambda: controller.calls.append(("upload_local_instagram_carousel",)),
    )
    monkeypatch.setenv("SKIP_SLOW_PRINT", "1")
    inputs = iter(["n"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    tasks.replay("ig_upload_demo")

    assert ("upload_local_instagram_carousel",) in controller.calls
