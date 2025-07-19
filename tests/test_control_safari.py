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


def test_control_safari(monkeypatch):
    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    key_inputs = iter(["1", "4", "6"])  # open, run_js, quit
    text_inputs = iter([
        "https://example.com",
        "2+2",
    ])
    monkeypatch.setattr(tasks, "_read_key", lambda: next(key_inputs))
    monkeypatch.setattr("builtins.input", lambda _: next(text_inputs))

    tasks.control_safari()

    assert ("open", "https://example.com") in controller.calls
    assert ("run_js", "2+2") in controller.calls
