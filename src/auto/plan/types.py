"""Data structures and helpers for automation plans."""

from __future__ import annotations

import json
import glob
import shutil
import subprocess
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any

import logging

logger = logging.getLogger(__name__)


@dataclass
class Step:
    """Represents one atomic automation step."""

    id: int
    type: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    selector: Optional[str] = None
    prompt_template: Optional[str] = None
    store_as: Optional[str] = None
    status: str = "pending"  # pending | success | failed | abandoned
    result: Optional[str] = None  # log of what happened
    dom_snapshot: Optional[str] = None  # path to saved DOM snapshot
    pre_conditions: List[str] = field(default_factory=list)
    post_conditions: List[str] = field(default_factory=list)


@dataclass
class Plan:
    objective: str
    steps: List[Step]


class PlanManager:
    """Handle reading, writing and backing up plan files."""

    def __init__(self, path: str, backup_dir: str = "backups", work_path: Optional[str] = None) -> None:
        self.src_path = path
        suffix = Path(path).suffix
        self.path = work_path or f"{Path(path).stem}_work{suffix}"
        self.backup_dir = Path(backup_dir)
        self._ensure_working_copy()

    def _ensure_working_copy(self) -> None:
        if not Path(self.path).exists() and Path(self.src_path).exists():
            shutil.copy(self.src_path, self.path)
            logger.info("Copied plan %s -> %s", self.src_path, self.path)

    def load(self) -> Plan:
        self._ensure_working_copy()
        data = json.load(open(self.path))
        steps = [Step(**s) for s in data.get("steps", [])]
        plan = Plan(objective=data.get("objective", ""), steps=steps)
        logger.info("Loaded plan: %s with %d steps", plan.objective, len(steps))
        return plan

    def save(self, plan: Plan) -> None:
        with open(self.path, "w") as f:
            json.dump({"objective": plan.objective, "steps": [asdict(s) for s in plan.steps]}, f, indent=2)
        logger.info("Saved plan to %s", self.path)
        commit_file(self.path, f"Update plan after changes at {datetime.now(timezone.utc).isoformat()}")

    def reset(self) -> None:
        artifacts = [self.path, "execution_log.json", "memory.json"]
        for art in artifacts:
            try:
                Path(art).unlink(missing_ok=True)
            except Exception as exc:  # pragma: no cover - best effort cleanup
                logger.warning("Failed to delete %s: %s", art, exc)
        for html in glob.glob("dom_step_*.html"):
            try:
                Path(html).unlink(missing_ok=True)
            except Exception as exc:  # pragma: no cover - best effort cleanup
                logger.warning("Failed to delete DOM snapshot %s: %s", html, exc)
        if self.backup_dir.is_dir():
            shutil.rmtree(self.backup_dir, ignore_errors=True)
        logger.info("Reset plan state and removed artifacts")

    def backup(self) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest = self.backup_dir / f"plan_{timestamp}.json"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.path, dest)
        logger.info("Backup of plan saved to %s", dest)

    def restore(self, step_id: int) -> Plan:
        plan = self.load()
        for step in plan.steps:
            if step.id >= step_id:
                step.status = "pending"
                step.result = None
                step.dom_snapshot = None
        self.save(plan)
        logger.info("Restored plan to step %d", step_id)
        return plan


def commit_file(path: str, message: str) -> None:
    """Commit a file to git if possible."""
    try:
        subprocess.run(["git", "add", path], check=True)
        subprocess.run(["git", "commit", "-m", message], check=True)
        logger.info("Committed %s: %s", path, message)
    except Exception as e:  # pragma: no cover - git may not be available
        logger.warning("Git commit failed for %s: %s", path, e)

