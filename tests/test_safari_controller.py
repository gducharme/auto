from auto.automation.safari import SafariController


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
