from invoke import Context
import tasks  # noqa: E402


class DummyController:
    def __init__(self, mergeable=True):
        self.calls = []
        self.mergeable = mergeable

    def open(self, url):
        self.calls.append(("open", url))
        return "OK"

    def run_js(self, code):
        self.calls.append(("run_js", code))
        if code == "document.documentElement.outerHTML":
            return (
                "<div><a href='/pr1'><span class='text-green-500'>+1</span></a></div>"
            )
        if "github.com" in code:
            return "https://github.com/user/repo/pull/1"
        if "button.js-merge-branch" in code:
            return "1" if self.mergeable else ""
        return ""

    def click(self, selector):
        self.calls.append(("click", selector))
        return "OK"

    def close_tab(self):
        self.calls.append(("close_tab",))
        return "OK"


def test_merge_bot_merges(monkeypatch):
    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setattr(tasks, "extract_links_with_green_span", lambda html: ["/pr1"])

    tasks.merge_bot(Context())

    assert ("click", "button.js-merge-branch") in controller.calls
    assert ("click", "#archive") in controller.calls


def test_merge_bot_skips_when_not_mergeable(monkeypatch):
    controller = DummyController(mergeable=False)
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setattr(tasks, "extract_links_with_green_span", lambda html: ["/pr1"])

    tasks.merge_bot(Context())

    assert ("click", "button.js-merge-branch") not in controller.calls
    assert ("click", "#all-done") in controller.calls


def test_merge_bot_no_pr(monkeypatch):
    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setattr(tasks, "extract_links_with_green_span", lambda html: [])

    tasks.merge_bot(Context())

    assert controller.calls == [
        ("open", "https://chatgpt.com/kodex"),
        ("run_js", "document.documentElement.outerHTML"),
    ]
