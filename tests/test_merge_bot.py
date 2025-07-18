from auto.cli import automation as tasks


class DummyController:
    def __init__(self, mergeable=True, github_link=True):
        self.calls = []
        self.mergeable = mergeable
        self.github_link = github_link

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
            return "https://github.com/user/repo/pull/1" if self.github_link else ""
        if "Create PR" in code:
            if "outerHTML" in code:
                return "<button>Create PR</button>"
            if "click" in code:
                return "clicked"
        if "Merge pull request" in code:
            if "outerHTML" in code:
                return "<button>Merge pull request</button>" if self.mergeable else ""
            if "click" in code:
                return "clicked" if self.mergeable else ""
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
    monkeypatch.setenv("TASKS_DELAY", "0")

    tasks.merge_bot()

    assert any(
        call[0] == "run_js" and "Merge pull request" in call[1] and "click" in call[1]
        for call in controller.calls
    )


def test_merge_bot_skips_when_not_mergeable(monkeypatch):
    controller = DummyController(mergeable=False)
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setattr(tasks, "extract_links_with_green_span", lambda html: ["/pr1"])
    monkeypatch.setenv("TASKS_DELAY", "0")

    tasks.merge_bot()

    assert not any(
        call[0] == "run_js" and "Merge pull request" in call[1] and "click" in call[1]
        for call in controller.calls
    )


def test_merge_bot_no_pr(monkeypatch):
    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setattr(tasks, "extract_links_with_green_span", lambda html: [])
    monkeypatch.setenv("TASKS_DELAY", "0")

    tasks.merge_bot()

    assert controller.calls == [
        ("open", "https://chatgpt.com/codex"),
        ("run_js", "document.documentElement.outerHTML"),
    ]


def test_merge_bot_create_pr_button(monkeypatch):
    controller = DummyController(github_link=False)
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setattr(tasks, "extract_links_with_green_span", lambda html: ["/pr1"])
    monkeypatch.setenv("TASKS_DELAY", "0")

    tasks.merge_bot()

    assert ("open", "https://chatgpt.com/pr1") in controller.calls
    assert any(
        call[0] == "run_js" and "Create PR" in call[1] and "outerHTML" in call[1]
        for call in controller.calls
    )
    assert any(
        call[0] == "run_js" and "Create PR" in call[1] and "click" in call[1]
        for call in controller.calls
    )
