from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List

# Constants used for parsing
HEADER_RE = re.compile(r"^(#+)\s+(.*)")
BULLET_RE = re.compile(r"^\s*[-*]\s+(.*)")
NUMBERED_RE = re.compile(r"^\s*(\d+)\.\s+(.*)")

DEFAULT_OUTPUT_DIR = Path("src/plan")


@dataclass
class Task:
    """Representation of a parsed plan task."""

    id: str
    heading: str
    text: str


def _write_tasks(tasks: Iterable[Task], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for task in tasks:
        path = out_dir / f"{task.id}.task"
        with path.open("w", encoding="utf-8") as fh:
            json.dump(asdict(task), fh, indent=2)


def parse_plan(plan_file: Path, out_dir: Path = DEFAULT_OUTPUT_DIR) -> List[Task]:
    """Parse a project plan into structured :class:`Task` objects.

    Parameters
    ----------
    plan_file:
        Path to the ``PLAN.md`` file.
    out_dir:
        Directory where ``*.task`` files will be written.

    Returns
    -------
    List[Task]
        Parsed tasks in the order they were encountered.
    """

    tasks: List[Task] = []
    heading_stack: List[tuple[int, str]] = []
    seq = 1

    with Path(plan_file).open(encoding="utf-8") as fh:
        for line in fh:
            if m := HEADER_RE.match(line):
                level = len(m.group(1))
                text = m.group(2).strip()
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()
                heading_stack.append((level, text))
                continue

            if m := NUMBERED_RE.match(line):
                text = m.group(2).strip()
            elif m := BULLET_RE.match(line):
                text = m.group(1).strip()
            else:
                continue


            item_id = str(seq)
            seq += 1

            heading = " / ".join(h[1] for h in heading_stack)
            tasks.append(Task(id=item_id, heading=heading, text=text))

    _write_tasks(tasks, out_dir)
    return tasks
