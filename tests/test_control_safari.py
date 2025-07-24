from auto.cli import automation as tasks
from pathlib import Path
import json
import shutil


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


def test_control_safari(monkeypatch, capsys):
    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setattr(tasks, "fetch_dom_html", lambda url=None: "<html></html>")

    key_inputs = iter(["0", "6", "b"])  # open, fetch_dom, quit
    text_inputs = iter(
        [
            "demo_test",
            "https://example.com",
        ]
    )
    monkeypatch.setattr(tasks, "_read_key", lambda: next(key_inputs))
    monkeypatch.setattr("builtins.input", lambda _: next(text_inputs))

    tasks.control_safari()

    captured = capsys.readouterr()

    assert ("open", "https://example.com") in controller.calls

    test_dir = Path("tests/fixtures/demo_test")
    assert (test_dir / "1.html").exists()
    log = json.loads((test_dir / "commands.json").read_text())
    assert log[0] == ["open", "https://example.com"]
    assert log[1] == ["fetch_dom", str(test_dir / "1.html")]

    out = captured.out
    assert "Command log:" in out

    shutil.rmtree(test_dir)


def test_control_safari_run_js_file(monkeypatch, tmp_path):
    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    js_path = tmp_path / "helper.js"
    js_code = "console.log('hello');"
    js_path.write_text(js_code)

    key_inputs = iter(["4", "b"])  # run_js_file, quit
    text_inputs = iter(
        [
            "demo_js",
            str(js_path),
        ]
    )
    monkeypatch.setattr(tasks, "_read_key", lambda: next(key_inputs))
    monkeypatch.setattr("builtins.input", lambda _: next(text_inputs))

    tasks.control_safari()

    assert ("run_js", js_code) in controller.calls
    shutil.rmtree(Path("tests/fixtures/demo_js"))


def test_control_safari_run_js_file_with_variable(monkeypatch, tmp_path):
    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setattr(tasks, "query_llm", lambda prompt: "42")

    js_path = tmp_path / "helper.js"
    js_path.write_text("console.log({{num}});")

    key_inputs = iter(["8", "4", "b"])  # llm_query, run_js_file, quit
    text_inputs = iter(
        [
            "demo_js_var",
            "meaning?",
            "num",
            str(js_path),
        ]
    )
    monkeypatch.setattr(tasks, "_read_key", lambda: next(key_inputs))
    monkeypatch.setattr("builtins.input", lambda _: next(text_inputs))

    tasks.control_safari()

    assert ("run_js", "console.log(42);") in controller.calls
    shutil.rmtree(Path("tests/fixtures/demo_js_var"))


def test_control_safari_run_applescript_file(monkeypatch, tmp_path):
    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)

    script_path = tmp_path / "helper.scpt"
    script_path.write_text('say "hello"')

    calls = []

    def fake_run(cmd, capture_output=True, text=True):
        calls.append(cmd)
        from subprocess import CompletedProcess

        return CompletedProcess(cmd, 0, stdout="OK", stderr="")

    monkeypatch.setattr(tasks.subprocess, "run", fake_run)

    key_inputs = iter(["5", "b"])  # run_applescript_file, quit
    text_inputs = iter(
        [
            "demo_scpt",
            str(script_path),
        ]
    )
    monkeypatch.setattr(tasks, "_read_key", lambda: next(key_inputs))
    monkeypatch.setattr("builtins.input", lambda _: next(text_inputs))

    tasks.control_safari()

    assert calls and calls[0][0] == "osascript"
    shutil.rmtree(Path("tests/fixtures/demo_scpt"))


def test_control_safari_run_applescript_file_with_variable(monkeypatch, tmp_path):
    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setattr(tasks, "query_llm", lambda prompt: "hi")

    script_path = tmp_path / "helper.scpt"
    script_path.write_text('say "{{word}}"')

    outputs = []

    def fake_run(cmd, capture_output=True, text=True):
        content = Path(cmd[1]).read_text()
        outputs.append(content)
        from subprocess import CompletedProcess

        return CompletedProcess(cmd, 0, stdout="OK", stderr="")

    monkeypatch.setattr(tasks.subprocess, "run", fake_run)

    key_inputs = iter(["8", "5", "b"])  # llm_query, run_applescript_file, quit
    text_inputs = iter(
        [
            "demo_scpt_var",
            "hello?",
            "word",
            str(script_path),
        ]
    )
    monkeypatch.setattr(tasks, "_read_key", lambda: next(key_inputs))
    monkeypatch.setattr("builtins.input", lambda _: next(text_inputs))

    tasks.control_safari()

    assert outputs and outputs[0] == 'say "hi"'
    shutil.rmtree(Path("tests/fixtures/demo_scpt_var"))


def test_control_safari_llm_query(monkeypatch):
    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setattr(tasks, "query_llm", lambda prompt: "pong")

    key_inputs = iter(["8", "b"])  # llm_query, quit
    text_inputs = iter(
        [
            "demo_llm",
            "ping?",
            "answer",
        ]
    )
    monkeypatch.setattr(tasks, "_read_key", lambda: next(key_inputs))
    monkeypatch.setattr("builtins.input", lambda _: next(text_inputs))

    tasks.control_safari()

    test_dir = Path("tests/fixtures/demo_llm")
    log = json.loads((test_dir / "commands.json").read_text())
    assert log == [["llm_query", "ping?", "pong", "answer"]]
    shutil.rmtree(test_dir)


def test_control_safari_fill_with_variable(monkeypatch):
    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setattr(tasks, "query_llm", lambda prompt: "hello")

    key_inputs = iter(["8", "2", "b"])  # llm_query, fill, quit
    text_inputs = iter(
        [
            "demo_fill_var",
            "ping",
            "msg",
            "#box",
            "{{msg}}",
        ]
    )
    monkeypatch.setattr(tasks, "_read_key", lambda: next(key_inputs))
    monkeypatch.setattr("builtins.input", lambda _: next(text_inputs))

    tasks.control_safari()

    assert ("fill", "#box", "hello") in controller.calls
    test_dir = Path("tests/fixtures/demo_fill_var")
    log = json.loads((test_dir / "commands.json").read_text())
    assert log == [["llm_query", "ping", "hello", "msg"], ["fill", "#box", "{{msg}}"]]
    shutil.rmtree(test_dir)


def test_control_safari_abort(monkeypatch):
    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)
    monkeypatch.setattr(tasks, "fetch_dom_html", lambda url=None: "<html></html>")

    key_inputs = iter(["c"])  # abort
    text_inputs = iter(
        [
            "demo_abort",
        ]
    )
    monkeypatch.setattr(tasks, "_read_key", lambda: next(key_inputs))
    monkeypatch.setattr("builtins.input", lambda _: next(text_inputs))

    tasks.control_safari()

    test_dir = Path("tests/fixtures/demo_abort")
    assert not test_dir.exists()


def test_control_safari_initial_vars(monkeypatch):
    controller = DummyController()
    monkeypatch.setattr(tasks, "SafariController", lambda: controller)

    recorded = {}

    def fake_menu(controller, test_dir, collected, step, variables):
        recorded.update(variables)
        return collected, step, True

    monkeypatch.setattr(tasks, "_interactive_menu", fake_menu)

    text_inputs = iter(
        [
            "demo_vars",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(text_inputs))

    tasks.control_safari(post_id="42", network="testnet")

    assert recorded["post_id"] == "42"
    assert recorded["network"] == "testnet"
    test_dir = Path("tests/fixtures/demo_vars")
    assert not test_dir.exists()


def test_interactive_menu_load_post(monkeypatch, test_db_engine, tmp_path):
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
    variables = {}

    key_inputs = iter(["a", "b"])  # load_post, quit
    text_inputs = iter(
        [
            "1",
            "mastodon",
        ]
    )
    monkeypatch.setattr(tasks, "_read_key", lambda: next(key_inputs))
    monkeypatch.setattr("builtins.input", lambda _: next(text_inputs))

    collected, step, aborted = tasks._interactive_menu(
        controller, tmp_path, [], 1, variables
    )

    assert not aborted
    assert step == 1
    assert collected == [["load_post", "1", "mastodon"]]
    assert variables["tweet"] == "Hello T"
