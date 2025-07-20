"""Safari automation and helper commands."""

from __future__ import annotations

from pathlib import Path
import subprocess
import json
import shutil

from typing import Optional

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
    response = dspy.chat(prompt)
    print(response)


@app.command()
def dspy_experiment() -> None:
    """Run the standalone dspy experiment script."""

    subprocess.run(["python", "src/experiments/dspy_exp.py"], check=True)


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


@app.command()
def control_safari() -> None:
    """Interactively control Safari via a menu loop."""

    test_name = input("Test name: ")
    fixtures_root = Path("tests/fixtures")
    test_dir = fixtures_root / test_name
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)

    controller = SafariController()
    commands = [
        ("open", "Open a URL"),
        ("click", "Click an element by CSS selector"),
        ("fill", "Fill a selector with text"),
        ("run_js", "Run arbitrary JavaScript"),
        ("fetch_dom", "Save page DOM to fixture"),
        ("close_tab", "Close the current tab"),
        ("quit", "Exit the menu"),
    ]

    collected: list[tuple[str, ...]] = []
    step = 1

    while True:
        print("\nAvailable commands:")
        for i, (_, desc) in enumerate(commands, 1):
            print(f"  {i}. {desc}")
        print("Select option [1-{}]: ".format(len(commands)), end="", flush=True)
        choice_idx = _read_key()
        print(choice_idx)  # echo the selected key
        if not choice_idx.isdigit() or not (1 <= int(choice_idx) <= len(commands)):
            print("Unknown command")
            continue

        choice, _ = commands[int(choice_idx) - 1]
        if choice == "quit":
            break
        elif choice == "open":
            url = input("URL: ")
            collected.append(("open", url))
            result = controller.open(url)
            if result:
                print(result)
        elif choice == "click":
            selector = input("Selector: ")
            collected.append(("click", selector))
            result = controller.click(selector)
            if result:
                print(result)
        elif choice == "fill":
            selector = input("Selector: ")
            text = input("Text: ")
            collected.append(("fill", selector, text))
            result = controller.fill(selector, text)
            if result:
                print(result)
        elif choice == "run_js":
            code = input("JavaScript: ")
            collected.append(("run_js", code))
            result = controller.run_js(code)
            if result:
                print(result)
        elif choice == "fetch_dom":
            dom = fetch_dom_html()
            dest = test_dir / f"{step}.html"
            dest.write_text(dom)
            collected.append(("fetch_dom", str(dest)))
            step += 1
            print(f"Saved DOM to {dest}")
        elif choice == "close_tab":
            collected.append(("close_tab",))
            result = controller.close_tab()
            if result:
                print(result)

    if collected:
        print("\nCommand log:")
        for entry in collected:
            print(" ".join(entry))
        (test_dir / "commands.json").write_text(json.dumps(collected, indent=2))


@app.command()
def replay(name: str = "facebook") -> None:
    """Replay recorded Safari commands from ``tests/fixtures/<name>``."""

    fixtures_root = Path("tests/fixtures")
    commands_path = fixtures_root / name / "commands.json"
    if not commands_path.exists():
        typer.echo(f"commands.json not found: {commands_path}")
        raise typer.Exit(1)

    commands: list[list[str]] = json.loads(commands_path.read_text())

    controller = SafariController()

    for entry in commands:
        cmd = entry[0]
        args = entry[1:]
        if cmd == "open" and args:
            url = args[0]
            _slow_print(f"Opening {url}")
            controller.open(url)
        elif cmd == "click" and args:
            selector = args[0]
            _slow_print(f"Clicking {selector}")
            controller.click(selector)
        elif cmd == "fill" and len(args) == 2:
            selector, text = args
            _slow_print(f"Filling {selector}")
            controller.fill(selector, text)
        elif cmd == "run_js" and args:
            _slow_print("Running JavaScript")
            controller.run_js(args[0])
        elif cmd == "close_tab":
            _slow_print("Closing tab")
            controller.close_tab()
        elif cmd == "fetch_dom" and args:
            dest = Path(args[0])
            dest.parent.mkdir(parents=True, exist_ok=True)
            dom = fetch_dom_html()
            dest.write_text(dom)
            _slow_print(f"Saved DOM to {dest}")
        else:
            typer.echo(f"Unknown command: {cmd}")
