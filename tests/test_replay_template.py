import shutil
from pathlib import Path

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
