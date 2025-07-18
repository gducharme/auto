from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List

from openai import OpenAI
from selenium import webdriver
from selenium.common.exceptions import WebDriverException


@dataclass
class Step:
    """Single action in a plan."""

    id: int
    description: str
    status: str = "pending"
    result: str | None = None
    dom_snapshot: str | None = None


@dataclass
class Plan:
    """High level objective and associated steps."""

    objective: str
    steps: List[Step]


class PlanManager:
    """Load and persist :class:`Plan` objects with optional backups."""

    def __init__(self, path: Path, backup_dir: Path | str = "backups") -> None:
        self.path = Path(path)
        self.backup_dir = Path(backup_dir)

    def load(self) -> Plan:
        data = json.loads(self.path.read_text())
        steps = [Step(**s) for s in data["steps"]]
        return Plan(objective=data["objective"], steps=steps)

    def save(self, plan: Plan) -> None:
        payload = {
            "objective": plan.objective,
            "steps": [asdict(s) for s in plan.steps],
        }
        self.path.write_text(json.dumps(payload, indent=2))

    def backup(self) -> None:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        dest = self.backup_dir / f"plan_{timestamp}.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(self.path, dest)
        print(f"[Backup] Saved plan state to {dest}")

    def restore(self, step_id: int) -> Plan:
        plan = self.load()
        for step in plan.steps:
            if step.id >= step_id:
                step.status = "pending"
                step.result = None
                step.dom_snapshot = None
        self.save(plan)
        print(f"[Restore] Rolled back to step {step_id}")
        return plan


class Planner:
    """Generate plans using a language model."""

    def __init__(self, llm_client: OpenAI) -> None:
        self.llm = llm_client

    def generate_plan(self, objective: str) -> Plan:
        prompt = (
            "Decompose the following objective into a numbered list of steps:\n"
            f"Objective: {objective}\n"
        )
        response = self.llm.complete(prompt)
        lines = response.splitlines()
        steps: List[Step] = []
        for i, line in enumerate(lines, start=1):
            if line.strip():
                steps.append(Step(id=i, description=line.strip()))
        return Plan(objective=objective, steps=steps)


class StepExecutor:
    """Execute plan steps using Selenium."""

    def __init__(self, max_retries: int = 3) -> None:
        self.driver: webdriver.Chrome | None = None
        self.max_retries = max_retries

    def __enter__(self) -> "StepExecutor":
        self.driver = webdriver.Chrome()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.driver:
            self.driver.quit()

    def execute(self, step: Step) -> Step:
        assert self.driver, "StepExecutor must be used as a context manager"
        attempt = 0
        while attempt < self.max_retries:
            attempt += 1
            try:
                desc = step.description.lower()
                if "navigate to" in desc:
                    url = step.description.split("navigate to", 1)[1].strip()
                    self.driver.get(url)
                    step.result = f"navigated to {url}"
                elif "click" in desc:
                    selector = step.description.split("click", 1)[1].strip()
                    elem = self.driver.find_element("css selector", selector)
                    elem.click()
                    step.result = f"clicked {selector}"
                else:
                    step.status = "failed"
                    step.result = "requires human input"
                    break

                step.status = "success"
            except (WebDriverException, Exception) as exc:
                step.status = "failed"
                step.result = f"Attempt {attempt}: {exc}"
                print(f"[Error] {step.result}")
                continue
            finally:
                try:
                    dom = self.driver.page_source
                    filename = f"dom_step_{step.id}_attempt_{attempt}.html"
                    Path(filename).write_text(dom, encoding="utf-8")
                    step.dom_snapshot = filename
                except Exception as dom_exc:
                    print(f"[Warning] Failed to save DOM: {dom_exc}")

            if step.status == "success":
                break

        return step


def run(plan_path: Path) -> None:
    manager = PlanManager(plan_path)

    try:
        plan = manager.load()
    except FileNotFoundError:
        llm = OpenAI(api_key="YOUR_KEY")
        planner = Planner(llm)
        plan = planner.generate_plan("Merge pull request")
        manager.save(plan)

    with StepExecutor() as executor:
        for step in plan.steps:
            if step.status == "pending":
                try:
                    manager.backup()
                except Exception:
                    pass

                updated = executor.execute(step)
                manager.save(plan)

                if updated.status != "success":
                    action = input(
                        f"Step {step.id} '{step.description}' failed."
                        " [r]ollback, [c]ontinue, or [q]uit? "
                    ).strip().lower()
                    if action.startswith("r"):
                        num = input("Enter step number to rollback to: ")
                        if num.isdigit():
                            plan = manager.restore(int(num))
                        continue
                    if action.startswith("q"):
                        print("Exiting. You can resume later.")
                        return
                    plan = manager.load()

    print("All steps complete!")


if __name__ == "__main__":
    import sys

    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("plan.json")
    run(path)
