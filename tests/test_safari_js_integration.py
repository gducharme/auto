from __future__ import annotations

import shutil
import sys
import time
import os
from pathlib import Path

import pytest

from auto.automation.safari import SafariController


@pytest.mark.integration
@pytest.mark.applescript
def test_safari_can_run_fixture_javascript_helpers():
    """Load a saved HTML fixture in Safari and execute replay JS helpers."""
    if (
        sys.platform != "darwin"
        or shutil.which("osascript") is None
        or os.getenv("RUN_APPLESCRIPT_TESTS") != "1"
    ):
        pytest.skip(
            "AppleScript tests require macOS + osascript + RUN_APPLESCRIPT_TESTS=1"
        )

    controller = SafariController()
    fixture = (
        Path(__file__).resolve().parent
        / "fixtures"
        / "js_integration"
        / "share_surface.html"
    )
    facebook_js = (
        Path(__file__).resolve().parent / "site_js" / "facebook.js"
    ).read_text()
    substack_js = (
        Path(__file__).resolve().parent / "site_js" / "substack.js"
    ).read_text()

    try:
        controller.open(fixture.resolve().as_uri())
    except RuntimeError as exc:
        pytest.skip(
            f"Safari AppleScript automation unavailable in this environment: {exc}"
        )
    ready = controller.run_js("document.readyState")
    assert ready in {"complete", "interactive"}

    controller.run_js(facebook_js)
    controller.run_js(substack_js)

    # Specialized click helper from facebook.js
    click_result = controller.run_js(
        "(() => { try { const r = clickExactInteractiveElementByTextFirst('Share'); return r ? 'clicked' : 'null'; } catch(e) { return 'ERR:' + e.message; } })()"
    )
    assert click_result == "clicked"
    clicked_share = "false"
    for _ in range(5):
        clicked_share = controller.run_js("String(Boolean(window.__shareClicked))")
        if clicked_share == "true":
            break
        time.sleep(0.1)
    assert clicked_share == "true"

    # Menu and indexed UFI helpers from substack.js
    controller.run_js("clickMenuItem('Get share images')")
    clicked_menu = controller.run_js("String(Boolean(window.__menuClicked))")
    assert clicked_menu == "true"

    controller.run_js("clickPostUfiButton(1)")
    clicked_ufi = controller.run_js("String(Boolean(window.__ufi1))")
    assert clicked_ufi == "true"

    controller.close_tab()
