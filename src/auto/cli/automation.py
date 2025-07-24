"""Safari automation and helper commands."""

from __future__ import annotations

from pathlib import Path
import subprocess
import json
import shutil

from typing import Optional, Iterable

import typer

from auto.cli.helpers import (
    _get_medium_magic_link,
    _slow_print,
    _delay,
    click_button_by_text,
)
from auto.html_helpers import fetch_dom as fetch_dom_html, count_link_states
from auto.html_utils import extract_links_with_green_span, parse_codex_tasks
from auto.automation.safari import SafariController


def _read_key() -> str:
    """Read a single character from stdin without requiring Enter.

    Any extra characters left in the input buffer (for example the newline
    from pressing ``Enter``) are discarded so that only one command is
    processed per selection.
    """

    import sys
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        try:
            termios.tcflush(fd, termios.TCIFLUSH)
        except termios.error:
            pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch


def _next_step(commands: Iterable[list[str]]) -> int:
    """Return the next DOM snapshot step for ``commands``."""

    numbers: list[int] = []
    for entry in commands:
        if entry and entry[0] == "fetch_dom" and len(entry) > 1:
            stem = Path(entry[1]).stem
            if stem.isdigit():
                numbers.append(int(stem))
    return max(numbers) + 1 if numbers else 1


def query_llm(prompt: str) -> str:
    """Return the response from a local LLM via dspy."""

    import dspy

    lm = dspy.LM("ollama_chat/gemma3:4b", api_base="http://localhost:11434", api_key="")
    dspy.configure(lm=lm)

    response = lm(messages=[{"role": "user", "content": prompt}])

    if isinstance(response, list):
        response = response[0]

    return str(response).strip()


app = typer.Typer(help="Automation commands")


@app.command()
def chat(
    message: Optional[str] = None,
    model: str = "gemma-3-27b-it-qat",
    api_base: str = "http://localhost:1234/v1",
    model_type: str = "chat",
) -> None:
    """Send a chat message to a local LLM via dspy."""

    import dspy

    lm = dspy.LM(model=model, api_base=api_base, api_key="", model_type=model_type)
    dspy.configure(lm=lm)

    default_question = "What is the typical silica (SiO₂) content in standard soda-lime glass, and how is it manufactured?"
    prompt = message or default_question
    response = lm(messages=[{"role": "user", "content": prompt}])
    print(response)


@app.command()
def dspy_experiment(post_id: Optional[str] = None) -> None:
    """Run the standalone dspy experiment script."""

    cmd = ["python", "src/experiments/dspy_exp.py"]
    if post_id is not None:
        cmd += ["--post-id", str(post_id)]
    subprocess.run(cmd, check=True)


@app.command()
def medium_magic_link() -> None:
    """Check Apple Mail once for a Medium magic link and print the result."""

    link = _get_medium_magic_link()
    if link:
        print(f"Found magic link: {link}")
    else:
        print("Magic link not found")


@app.command()
def safari_fill(url: str, selector: str, text: str) -> None:
    """Open or activate a Safari tab and type text into the given field."""

    controller = SafariController()
    controller.open(url)
    result = controller.fill(selector, text)
    if result:
        print(result)


@app.command()
def codex_todo() -> None:
    """Open the ChatGPT Codex, prefill the TODO prompt and click ``Code``."""

    controller = SafariController()
    controller.open("https://chatgpt.com/codex")
    fill_result = controller.fill(
        "#prompt-textarea",
        "Tackle the top item in the TODO.md file. When the PR is complete, remove that item",
    )
    if fill_result:
        print(fill_result)

    js_click_code = (
        "const candidates=document.querySelectorAll('div.flex.items-center.justify-center');"
        "console.log('🔍 Found',candidates.length,'candidates:',candidates);"
        "const codeButton=Array.from(candidates).find(el=>{"
        "const t=el.innerText.trim();"
        "console.log('   • candidate text:',JSON.stringify(t));"
        "return t==='Code';});"
        "if(codeButton){"
        "codeButton.click();"
        "console.log('✅ Clicked the Code button!');"
        "}else{"
        "console.warn('❌ No matching Code button found—check the debug log above.');"
        "}"
    )

    js_result = controller.run_js(js_click_code)
    if js_result:
        print(js_result)


@app.command()
def fetch_dom(url: Optional[str] = None) -> None:
    """Print the DOM for the current tab or ``url``."""

    dom = fetch_dom_html(url)
    if dom:
        print(dom)
        dest = Path("tests/fixtures/dom.html")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(dom)


@app.command()
def count_links(url: str = "https://chatgpt.com/codex") -> None:
    """Download ``url`` and report merged vs active link counts."""

    dom = fetch_dom_html(url)
    merged, active = count_link_states(dom)
    print(f"Merged links: {merged}")
    print(f"Active tasks: {active}")


@app.command()
def merge_bot(codex_url: str = "https://chatgpt.com/codex") -> None:
    """Automatically merge ready PRs from the Codex page."""

    controller = SafariController()

    _slow_print(f"Opening Codex page: {codex_url}")
    controller.open(codex_url)

    _slow_print("Fetching DOM")
    dom = controller.run_js("document.documentElement.outerHTML")
    _slow_print("Extracting links")
    links = extract_links_with_green_span(dom)
    if not links:
        _slow_print("No pull request ready")
        return

    pr_url = links[0]
    if not pr_url.startswith("http"):
        from urllib.parse import urljoin

        pr_url = urljoin(codex_url, pr_url)

    _slow_print(f"Opening PR link: {pr_url}")
    controller.open(pr_url)

    if not click_button_by_text(controller, "View PR"):
        _slow_print("View PR button not found; trying to create PR")
        if not click_button_by_text(controller, "Create PR"):
            _slow_print("Create PR button not found")
            return
        _slow_print("Waiting for PR creation")
        _delay(15)
        click_button_by_text(controller, "View PR")

    _delay(5)
    if click_button_by_text(controller, "Merge pull request"):
        _slow_print("Clicked merge button")
    else:
        _slow_print("Merge button not found")


@app.command()
def github_bot(codex_url: str = "https://chatgpt.com/codex") -> None:
    """Open Codex and click the first button with a span containing 'Open'."""

    controller = SafariController()

    _slow_print(f"Opening Codex page: {codex_url}")
    controller.open(codex_url)

    _slow_print("Fetching DOM")
    dom = controller.run_js("document.documentElement.outerHTML")
    _slow_print("Scanning for Open button")

    tasks = parse_codex_tasks(dom)
    if not any(t["status"] == "Open" for t in tasks):
        _slow_print("Open button not found")
        return

    click_js = """
(() => {
  const span = Array.from(document.querySelectorAll('button span'))
    .find(el => el.textContent.includes('Open'));
  if (span) {
    span.closest('button').click();
    return 'clicked';
  }
  return '';
})()
"""
    if controller.run_js(click_js):
        _slow_print("Clicked Open button")
    else:
        _slow_print("Failed to click Open button")


@app.command()
def test_task(codex_url: str = "https://chatgpt.com/codex") -> None:
    """Open Codex then send an ``'f'`` keypress via JavaScript."""

    controller = SafariController()

    _slow_print(f"Opening Codex page: {codex_url}")
    controller.open(codex_url)

    _slow_print("Sending 'f' key")
    js = """
(() => {
  const evtInit = {key: 'f', code: 'KeyF', keyCode: 70, which: 70, bubbles: true};
  document.dispatchEvent(new KeyboardEvent('keydown', evtInit));
  document.dispatchEvent(new KeyboardEvent('keyup', evtInit));
  return 'sent';
})()
"""
    controller.run_js(js)


def _interactive_menu(
    controller: SafariController,
    test_dir: Path,
    collected: list[list[str]],
    step: int,
    variables: dict[str, str] | None = None,
) -> tuple[list[list[str]], int, bool]:
    """Run the interactive Safari control menu."""

    commands = [
        ("open", "Open a URL"),
        ("click", "Click an element by CSS selector"),
        ("fill", "Fill a selector with text"),
        ("run_js", "Run arbitrary JavaScript"),
        ("run_js_file", "Run JavaScript from a file"),
        ("run_applescript_file", "Run AppleScript from a file"),
        ("fetch_dom", "Save page DOM to fixture"),
        ("close_tab", "Close the current tab"),
        ("llm_query", "Send a prompt to the local LLM"),
        ("read_var", "Print a stored variable"),
        ("load_post", "Load a post preview"),
        ("quit", "Save and exit"),
        ("abort", "Exit without saving"),
    ]

    hex_keys = "0123456789abcdef"  # menu uses hexadecimal ordering 0-9 then a-f

    if variables is None:
        variables = {}

    def _render(template: str) -> str:
        from jinja2 import Template

        try:
            return Template(template).render(**variables)
        except Exception:
            return template

    aborted = False

    while True:
        print("\nAvailable commands:")
        for i, (_, desc) in enumerate(commands):
            key = hex_keys[i]
            print(f"  {key}. {desc}")
        last_key = hex_keys[len(commands) - 1]
        print(f"Select option [0-{last_key}]: ", end="", flush=True)
        choice_idx = _read_key().lower()
        print(choice_idx)  # echo the selected key
        if choice_idx not in hex_keys[: len(commands)]:
            print("Unknown command")
            continue

        choice, _ = commands[int(choice_idx, 16)]
        if choice == "quit":
            break
        elif choice == "abort":
            aborted = True
            break
        elif choice == "open":
            url = input("URL: ")
            collected.append(["open", url])
            result = controller.open(_render(url))
            if result:
                print(result)
        elif choice == "click":
            selector = input("Selector: ")
            collected.append(["click", selector])
            result = controller.click(_render(selector))
            if result:
                print(result)
        elif choice == "fill":
            selector = input("Selector: ")
            text = input("Text: ")
            collected.append(["fill", selector, text])
            result = controller.fill(_render(selector), _render(text))
            if result:
                print(result)
        elif choice == "run_js":
            code = input("JavaScript: ")
            collected.append(["run_js", code])
            result = controller.run_js(_render(code))
            if result:
                print(result)
        elif choice == "run_js_file":
            path_str = input("JS file path: ")
            path = Path(path_str)
            code = path.read_text()
            collected.append(["run_js_file", path_str])
            result = controller.run_js(_render(code))
            if result:
                print(result)
        elif choice == "run_applescript_file":
            path_str = input("AppleScript file path: ")
            path = Path(path_str)
            collected.append(["run_applescript_file", path_str])
            code = path.read_text()
            rendered = _render(code)
            import tempfile
            import os

            with tempfile.NamedTemporaryFile("w", suffix=".scpt", delete=False) as tmp:
                tmp.write(rendered)
                temp_path = tmp.name
            proc = subprocess.run(
                [
                    "osascript",
                    temp_path,
                ],
                capture_output=True,
                text=True,
            )
            os.unlink(temp_path)
            if proc.returncode == 0:
                out = proc.stdout.strip()
                if out:
                    print(out)
            else:
                print(proc.stderr.strip())
        elif choice == "fetch_dom":
            dom = fetch_dom_html()
            dest = test_dir / f"{step}.html"
            dest.write_text(dom)
            collected.append(["fetch_dom", str(dest)])
            step += 1
            print(f"Saved DOM to {dest}")
        elif choice == "close_tab":
            collected.append(["close_tab"])
            result = controller.close_tab()
            if result:
                print(result)
        elif choice == "llm_query":
            prompt = input("Prompt: ")
            response = query_llm(prompt)
            if response:
                print(response)
            name = input("store_as (optional): ").strip()
            entry = ["llm_query", prompt, response]
            if name:
                variables[name] = response
                entry.append(name)
            collected.append(entry)
        elif choice == "read_var":
            name = input("Variable name: ")
            print(variables.get(name, ""))
        elif choice == "load_post":
            post_id = input("Post ID: ")
            network = input("Network [mastodon]: ").strip() or "mastodon"
            from auto.db import SessionLocal
            from auto.models import PostPreview, Post
            from jinja2 import Template

            with SessionLocal() as session:
                preview = session.get(
                    PostPreview, {"post_id": post_id, "network": network}
                )
                post = session.get(Post, post_id)

            if preview and post:
                variables["tweet"] = Template(preview.content).render(post=post)
                print("Preview loaded into variables['tweet']")
                collected.append(["load_post", post_id, network])
            else:
                print("Post or preview not found")

    return collected, step, aborted


@app.command()
def control_safari(post_id: Optional[str] = None, network: str = "mastodon") -> None:
    """Interactively control Safari via a menu loop."""

    test_name = input("Test name: ")
    fixtures_root = Path("tests/fixtures")
    test_dir = fixtures_root / test_name
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)

    controller = SafariController()
    collected: list[list[str]] = []
    variables: dict[str, str] = {}
    if post_id is not None:
        variables["post_id"] = post_id
    if network:
        variables["network"] = network
    collected, _, aborted = _interactive_menu(
        controller, test_dir, collected, 1, variables
    )

    if aborted:
        shutil.rmtree(test_dir)
        return

    if collected:
        print("\nCommand log:")
        for entry in collected:
            print(" ".join(entry))
        (test_dir / "commands.json").write_text(json.dumps(collected, indent=2))


@app.command()
def replay(
    name: str = "facebook",
    post_id: Optional[str] = None,
    network: str = "mastodon",
) -> None:
    """Replay recorded Safari commands from ``tests/fixtures/<name>``.

    DOM snapshots are written to that same directory regardless of the paths
    stored in the ``commands.json`` file.
    """

    fixtures_root = Path("tests/fixtures")
    commands_path = fixtures_root / name / "commands.json"
    if not commands_path.exists():
        typer.echo(f"commands.json not found: {commands_path}")
        raise typer.Exit(1)

    commands: list[list[str]] = json.loads(commands_path.read_text())

    controller = SafariController()

    variables: dict[str, str] = {"name": name}
    if post_id is not None:
        variables["post_id"] = post_id
    if network:
        variables["network"] = network

    def _render(template: str) -> str:
        from jinja2 import Template

        try:
            return Template(template).render(**variables)
        except Exception:
            return template

    for entry in commands:
        cmd = entry[0]
        args = entry[1:]
        if cmd == "open" and args:
            url = _render(args[0])
            _slow_print(f"Opening {url}")
            controller.open(url)
        elif cmd == "click" and args:
            selector = _render(args[0])
            _slow_print(f"Clicking {selector}")
            controller.click(selector)
        elif cmd == "fill" and len(args) == 2:
            selector, text = args
            selector = _render(selector)
            text = _render(text)
            _slow_print(f"Filling {selector}")
            controller.fill(selector, text)
        elif cmd == "run_js" and args:
            code = _render(args[0])
            _slow_print("Running JavaScript")
            controller.run_js(code)
        elif cmd == "run_js_file" and args:
            path = Path(args[0])
            if path.exists():
                _slow_print(f"Running JavaScript from {path}")
                controller.run_js(path.read_text())
            else:
                typer.echo(f"JS file not found: {path}")
        elif cmd == "run_applescript_file" and args:
            path = Path(args[0])
            if path.exists():
                _slow_print(f"Running AppleScript from {path}")
                proc = subprocess.run(
                    ["osascript", str(path)], capture_output=True, text=True
                )
                if proc.returncode != 0:
                    typer.echo(proc.stderr.strip())
                elif proc.stdout:
                    typer.echo(proc.stdout.strip())
            else:
                typer.echo(f"AppleScript file not found: {path}")
        elif cmd == "close_tab":
            _slow_print("Closing tab")
            controller.close_tab()
        elif cmd == "llm_query" and len(args) >= 2:
            response = args[1]
            store_as = args[2] if len(args) > 2 else None
            _slow_print(f"LLM response: {response}")
            if store_as:
                variables[store_as] = response
        elif cmd == "fetch_dom" and args:
            src_path = Path(args[0])
            dest = fixtures_root / name / src_path.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dom = fetch_dom_html()
            dest.write_text(dom)
            _slow_print(f"Saved DOM to {dest}")
        else:
            typer.echo(f"Unknown command: {cmd}")

    cont = input("Continue recording? [y/N]: ").strip().lower() == "y"
    if cont:
        step = _next_step(commands)
        test_dir = fixtures_root / name
        updated, _, aborted = _interactive_menu(
            controller, test_dir, commands, step, variables
        )
        if aborted:
            return
        if updated:
            commands_path.write_text(json.dumps(updated, indent=2))
