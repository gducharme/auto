from pathlib import Path
from auto.automation.plan_executor import StepExecutor, Step

class DummySafari:
    def __init__(self):
        self.calls = []
    def open(self, url: str) -> str:
        self.calls.append(("open", url))
        return "OK"
    def click(self, selector: str) -> str:
        self.calls.append(("click", selector))
        return "OK"
    def run_js(self, code: str) -> str:
        self.calls.append(("run_js", code))
        if "document.querySelector" in code:
            return "1" if "#exists" in code else ""
        if code == "window.location.href":
            return "https://example.com/page"
        if "document.documentElement.outerHTML" in code:
            return "<html></html>"
        return ""

def test_step_executor_uses_safari(tmp_path):
    safari = DummySafari()
    executor = StepExecutor(controller=safari, artifact_dir=str(tmp_path))

    step_nav = Step(id=1, type="navigate", url="https://example.com")
    result_nav = executor.execute(step_nav)
    assert ("open", "https://example.com") in safari.calls
    assert result_nav.status == "success"

    step_click = Step(id=2, type="click", selector="#btn")
    result_click = executor.execute(step_click)
    assert ("click", "#btn") in safari.calls
    assert result_click.status == "success"
    assert Path(result_click.dom_snapshot).exists()
