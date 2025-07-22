from auto.automation.plan_executor import StepExecutor
from auto.plan.types import Step
from auto.automation.safari import SafariController
from auto.automation.fixtures import load_commands


class DummyController:
    def __init__(self):
        self.calls = []

    def open(self, url):
        self.calls.append(("open", url))

    def click(self, sel):
        self.calls.append(("click", sel))

    def fill(self, sel, text):
        self.calls.append(("fill", sel, text))

    def run_js(self, code):
        self.calls.append(("run_js", code))

    def close_tab(self):
        self.calls.append(("close_tab",))


def test_load_commands_with_vars(tmp_path):
    cmds = load_commands("param", variables={"path": "foo", "selector": "#btn"})
    assert cmds[0][1] == "https://example.com/foo"
    assert cmds[1][1] == "#btn"


def test_run_fixture(monkeypatch):
    controller = DummyController()
    monkeypatch.setattr(SafariController, "__init__", lambda self: None)
    monkeypatch.setattr(SafariController, "open", controller.open)
    monkeypatch.setattr(SafariController, "click", controller.click)
    exec = StepExecutor(controller=SafariController())
    step = Step(
        id=1,
        type="run_fixture",
        fixture="param",
        vars={"path": "foo", "selector": "#btn"},
    )
    exec.execute(step)
    assert controller.calls == [
        ("open", "https://example.com/foo"),
        ("click", "#btn"),
    ]
