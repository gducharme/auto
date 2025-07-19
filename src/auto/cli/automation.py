"""Safari automation and helper commands."""

from __future__ import annotations

from pathlib import Path
import subprocess

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
def fetch_dom() -> None:
    """Open the Codex page and print the full DOM tree."""

    dom = fetch_dom_html()
    if dom:
        print(dom)
        dest = Path("tests/fixtures/dom.html")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(dom)


@app.command()
def count_links(url: str = "https://chatgpt.com/codex") -> None:
    """Download ``url`` and report merged vs active link counts."""

    dom = fetch_dom_html()
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
