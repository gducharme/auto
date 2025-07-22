from datetime import datetime, timezone

from auto.automation.plan_executor import StepExecutor
from auto.plan.types import Step
from auto.models import Post, PostPreview, PostStatus


class DummySafari:
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
        return "<html></html>"

    def close_tab(self):
        self.calls.append(("close_tab",))
        return "OK"


def test_compose_post_step(session, tmp_path):
    # create post, status and preview
    post = Post(id="1", title="Title", link="http://example", summary="", published="")
    status = PostStatus(post_id="1", network="mastodon", scheduled_at=datetime.now(timezone.utc))
    preview = PostPreview(
        post_id="1", network="mastodon", content="{{ post.title }} {{ post.link }}"
    )
    session.add_all([post, status, preview])
    session.commit()

    step = Step(id=1, type="compose_post", post_id="1", network="mastodon", tags_var="tags", store_as="final")
    executor = StepExecutor(controller=DummySafari(), snapshot_dir=tmp_path)
    executor.variables["tags"] = ["#python", "#coding"]

    updated = executor.execute(step)

    assert updated.status == "success"
    assert executor.variables["final"] == "Title http://example #python #coding"
