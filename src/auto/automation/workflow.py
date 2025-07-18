"""Simple GitHub pull request workflow automation."""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Dict

from ..html_helpers import fetch_dom
from ..html_utils import extract_links_with_green_span, parse_codex_tasks
from pathlib import Path

from .safari import SafariController


class WorkflowState(str, Enum):
    FETCH_DOM = "FETCH_DOM"
    PARSE_TASKS = "PARSE_TASKS"
    OPEN_PR = "OPEN_PR"
    MERGE_PR = "MERGE_PR"


WORKFLOW_DIR = Path("workflow")


def _load_payload(path: Path) -> Dict[str, Any]:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            pass
    return {}


def _save_payload(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def _run_state(payload: Dict[str, Any], controller: SafariController) -> WorkflowState:
    state = WorkflowState(payload.get("state", WorkflowState.FETCH_DOM))

    if state == WorkflowState.FETCH_DOM:
        dom = fetch_dom()
        payload["dom"] = dom
        next_state = WorkflowState.PARSE_TASKS

    elif state == WorkflowState.PARSE_TASKS:
        dom = payload.get("dom", "")
        payload["tasks"] = parse_codex_tasks(dom)
        links = extract_links_with_green_span(dom)
        payload["pr_url"] = links[0] if links else None
        next_state = WorkflowState.OPEN_PR

    elif state == WorkflowState.OPEN_PR:
        pr_url = payload.get("pr_url")
        if pr_url:
            controller.open(pr_url)
        next_state = WorkflowState.MERGE_PR

    else:  # MERGE_PR
        controller.run_js("document.querySelector('button.js-merge-branch')?.click();")
        next_state = WorkflowState.FETCH_DOM

    payload["state"] = next_state.value
    return next_state


def execute(workflow_id: str = "default") -> WorkflowState:
    """Execute the next step for ``workflow_id``."""

    path = WORKFLOW_DIR / f"{workflow_id}.json"
    payload = _load_payload(path)
    controller = SafariController()
    next_state = _run_state(payload, controller)
    payload["state"] = next_state.value
    _save_payload(path, payload)
    return next_state
