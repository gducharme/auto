"""Logging utilities for plan execution."""

from __future__ import annotations

import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Initialize logging when the plan executor starts."""
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            filename="agent.log",
            filemode="a",
        )


class ExecutionLogger:
    """Persist structured events from plan execution."""

    def __init__(self, path: str = "execution_log.json") -> None:
        self.path = path
        try:
            with open(self.path, "r") as f:
                self.events = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.events = []

    def log_event(self, event: Dict) -> None:
        self.events.append(event)
        with open(self.path, "w") as f:
            json.dump(self.events, f, indent=2)
        logger.info("Logged event: %s", event)


class MemoryModule:
    """Track step statistics across runs."""

    def __init__(self, path: str = "memory.json") -> None:
        self.path = path
        try:
            with open(self.path, "r") as f:
                self.memory = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.memory = {"step_stats": {}}

    def record_event(self, event: Dict) -> None:
        sid = str(event["step_id"])
        stats = self.memory["step_stats"].setdefault(
            sid, {"success": 0, "failed": 0, "abandoned": 0}
        )
        status = event.get("status")
        if status in stats:
            stats[status] += 1
        with open(self.path, "w") as f:
            json.dump(self.memory, f, indent=2)
        logger.info("Updated memory for step %s: %s", sid, stats)
