from auto.automation.safari import SafariController
import pytest
import sys
import shutil


def _fake_run(calls):
    def runner(cmd, capture_output=True, text=True):
        calls.append(cmd)
        from subprocess import CompletedProcess

        return CompletedProcess(cmd, 0, stdout="OK", stderr="")

    return runner


def test_open(monkeypatch):
    calls = []
    monkeypatch.setattr("subprocess.run", _fake_run(calls))
    controller = SafariController()
    controller.open("https://example.com")
    expected = [
        "osascript",
        str(controller.script),
        "open",
        "https://example.com",
    ]
    assert calls == [expected]


def test_click(monkeypatch):
    calls = []
    monkeypatch.setattr("subprocess.run", _fake_run(calls))
    controller = SafariController()
    controller.click("#btn")
    expected = ["osascript", str(controller.script), "click", "#btn"]
    assert calls == [expected]


def test_fill(monkeypatch):
    calls = []
    monkeypatch.setattr("subprocess.run", _fake_run(calls))
    controller = SafariController()
    controller.fill("input", "hello")
    expected = ["osascript", str(controller.script), "fill", "input", "hello"]
    assert calls == [expected]


def test_run_js(monkeypatch):
    calls = []
    monkeypatch.setattr("subprocess.run", _fake_run(calls))
    controller = SafariController()
    controller.run_js("2+2")
    expected = ["osascript", str(controller.script), "run_js", "2+2"]
    assert calls == [expected]


def test_close_tab(monkeypatch):
    calls = []
    monkeypatch.setattr("subprocess.run", _fake_run(calls))
    controller = SafariController()
    controller.close_tab()
    expected = ["osascript", str(controller.script), "close_tab"]
    assert calls == [expected]


@pytest.mark.integration
def test_startpage_search():
    """Open Startpage and submit a search via Safari."""
    if sys.platform != "darwin" or shutil.which("osascript") is None:
        pytest.skip("Safari integration requires macOS and osascript")

    controller = SafariController()
    assert controller.open("https://www.startpage.com") == "OK"
    assert controller.fill("#q", "what is the best season to fish in NC?") == "OK"
    assert (
        controller.run_js(
            "var b=document.querySelector('button[type='submit']');if(b)b.click();"
        )
        == "OK"
    )
    assert controller.close_tab() == "OK"
