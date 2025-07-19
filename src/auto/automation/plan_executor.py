import json
import shutil
import subprocess
import logging
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from openai import OpenAI  # pseudo-import for LLM planning
from .safari import SafariController

# ─── Logging Configuration ─────────────────────────────────────────────────────
DATA_DIR = Path("automation_data")
DATA_DIR.mkdir(exist_ok=True, parents=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filename=str(DATA_DIR / "agent.log"),
    filemode="a",
)
logger = logging.getLogger(__name__)


# ─── Data Structures ───────────────────────────────────────────────────────────
@dataclass
class Step:
    """Represents one atomic automation step."""

    id: int
    # New flexible fields allow multiple plan formats. "type" is used by
    # newer JSON plans while "description" supports older free-form steps.
    type: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    selector: Optional[str] = None
    prompt_template: Optional[str] = None
    store_as: Optional[str] = None
    status: str = "pending"  # pending | success | failed | abandoned
    result: Optional[str] = None  # log of what happened
    dom_snapshot: Optional[str] = None  # path to saved DOM snapshot
    pre_conditions: List[str] = field(default_factory=list)  # CSS selectors or checks
    post_conditions: List[str] = field(default_factory=list)  # CSS selectors or checks


@dataclass
class Plan:
    objective: str
    steps: List[Step]


# ─── Execution Logger ──────────────────────────────────────────────────────────
class ExecutionLogger:
    def __init__(self, path: str = str(DATA_DIR / "execution_log.json")):
        self.path = path
        try:
            with open(self.path, "r") as f:
                self.events = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.events = []

    def log_event(self, event: Dict):
        self.events.append(event)
        with open(self.path, "w") as f:
            json.dump(self.events, f, indent=2)
        logger.info(f"Logged event: {event}")


# ─── Memory Module ─────────────────────────────────────────────────────────────
class MemoryModule:
    def __init__(self, path: str = str(DATA_DIR / "memory.json")):
        self.path = path
        try:
            with open(self.path, "r") as f:
                self.memory = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.memory = {"step_stats": {}}

    def record_event(self, event: Dict):
        sid = str(event["step_id"])
        stats = self.memory["step_stats"].setdefault(
            sid, {"success": 0, "failed": 0, "abandoned": 0}
        )
        status = event.get("status")
        if status in stats:
            stats[status] += 1
        # persist memory
        with open(self.path, "w") as f:
            json.dump(self.memory, f, indent=2)
        logger.info(f"Updated memory for step {sid}: {stats}")


# ─── Git Versioning Utility ────────────────────────────────────────────────────
def commit_file(path: str, message: str):
    try:
        subprocess.run(["git", "add", path], check=True)
        subprocess.run(["git", "commit", "-m", message], check=True)
        logger.info(f"Committed {path}: {message}")
    except Exception as e:
        logger.warning(f"Git commit failed for {path}: {e}")


# ─── Plan Management ────────────────────────────────────────────────────────────
class PlanManager:
    def __init__(self, path: str = str(DATA_DIR / "plan.json"), backup_dir: str = str(DATA_DIR / "backups")):
        self.path = path
        self.backup_dir = backup_dir
        Path(self.backup_dir).mkdir(exist_ok=True, parents=True)

    def load(self) -> Plan:
        data = json.load(open(self.path))
        steps = [Step(**s) for s in data.get("steps", [])]
        plan = Plan(objective=data.get("objective", ""), steps=steps)
        logger.info(f"Loaded plan: {plan.objective} with {len(steps)} steps")
        return plan

    def save(self, plan: Plan):
        with open(self.path, "w") as f:
            json.dump(
                {"objective": plan.objective, "steps": [asdict(s) for s in plan.steps]},
                f,
                indent=2,
            )
        logger.info(f"Saved plan to {self.path}")
        commit_file(
            self.path, f"Update plan after changes at {datetime.now().isoformat()}"
        )

    def backup(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = f"{self.backup_dir}/plan_{timestamp}.json"
        shutil.copy(self.path, dest)
        logger.info(f"Backup of plan saved to {dest}")

    def restore(self, step_id: int) -> Plan:
        plan = self.load()
        for step in plan.steps:
            if step.id >= step_id:
                step.status = "pending"
                step.result = None
                step.dom_snapshot = None
        self.save(plan)
        logger.info(f"Restored plan to step {step_id}")
        return plan


# ─── Planner (retro-causal “look-ahead”) ────────────────────────────────────────
class Planner:
    def __init__(self, llm_client: OpenAI):
        self.llm = llm_client

    def generate_plan(self, objective: str) -> Plan:
        prompt = (
            f"Decompose the following objective into a numbered list of atomic steps:\n"
            f"Objective: {objective}\n"
        )
        response = self.llm.complete(prompt)
        lines = response.splitlines()
        steps = [
            Step(id=i, description=line.strip())
            for i, line in enumerate(lines, 1)
            if line.strip()
        ]
        plan = Plan(objective=objective, steps=steps)
        logger.info(f"Generated new plan: {objective} with {len(steps)} steps")
        return plan


# ─── Executor with Pre/Post Condition Checks & Logging ─────────────────────────
class StepExecutor:
    def __init__(
        self,
        controller: Optional[SafariController] = None,
        artifact_dir: str = str(DATA_DIR),
        max_retries: int = 3,
    ):
        self.controller = controller or SafariController()
        self.max_retries = max_retries
        self.artifact_dir = Path(artifact_dir)
        self.artifact_dir.mkdir(exist_ok=True, parents=True)
        # simple in-memory variable store for discovery steps
        self.variables: Dict[str, Any] = {}

    def _render(self, template: str) -> str:
        """Render a template string using variables from previous steps."""
        from jinja2 import Template

        try:
            tmpl = Template(template)
            return tmpl.render(**self.variables)
        except Exception as e:
            logger.error(f"Template render failed for '{template}': {e}")
            return template

    def check_pre_conditions(self, step: Step) -> bool:
        for cond in step.pre_conditions:
            logger.info(f"Checking pre-condition '{cond}' for step {step.id}")
            js = f"document.querySelector({json.dumps(cond)}) ? '1' : ''"
            if not self.controller.run_js(js):
                logger.error(f"Pre-condition '{cond}' failed")
                return False
        return True

    def check_post_conditions(self, step: Step) -> bool:
        for cond in step.post_conditions:
            logger.info(f"Checking post-condition '{cond}' for step {step.id}")
            if cond.startswith("url_contains:"):
                expected = cond.split(":", 1)[1].strip()
                current = self.controller.run_js("window.location.href")
                if expected not in current:
                    logger.error(
                        f"Post-condition '{cond}' failed: URL does not contain {expected}"
                    )
                    return False
            else:
                js = f"document.querySelector({json.dumps(cond)}) ? '1' : ''"
                if not self.controller.run_js(js):
                    logger.error(f"Post-condition '{cond}' failed")
                    return False
        return True

    def execute(self, step: Step) -> Step:
        description = step.description or step.type or "(unknown)"
        logger.info(f"Starting Step {step.id}: {description}")

        if step.pre_conditions and not self.check_pre_conditions(step):
            step.status = "failed"
            step.result = "pre-condition check failed"
            return step

        attempt = 0
        while attempt < self.max_retries and step.status == "pending":
            attempt += 1
            try:
                # Support old description-based steps as a fallback
                if step.type is None and step.description:
                    desc = step.description.lower()
                    if "navigate to" in desc:
                        step.type = "navigate"
                        step.url = desc.split("navigate to", 1)[1].strip()
                    elif "click" in desc:
                        step.type = "click"
                        step.selector = desc.split("click", 1)[1].strip()

                if step.type == "navigate" and step.url:
                    url = self._render(step.url)
                    self.controller.open(url)
                    step.result = f"opened {url}"
                elif step.type == "click" and step.selector:
                    selector = self._render(step.selector)
                    self.controller.click(selector)
                    step.result = f"clicked {selector}"
                elif step.type == "discover" and step.prompt_template:
                    # Real implementation would call an LLM with DOM and the prompt
                    dom = self.controller.run_js("document.documentElement.outerHTML")
                    rendered = self._render(step.prompt_template)
                    logger.debug(f"Discovery prompt: {rendered[:100]}")
                    # Placeholder: store empty list
                    selectors: List[str] = []
                    if step.store_as:
                        self.variables[step.store_as] = selectors
                    step.result = f"discovered {len(selectors)} selectors"
                else:
                    step.status = "failed"
                    step.result = "unsupported step type"
                    break

                if step.post_conditions and not self.check_post_conditions(step):
                    step.status = "failed"
                    step.result = "post-condition check failed"
                    logger.error(f"Step {step.id} post-condition check failed")
                    continue

                step.status = "success"
                logger.info(f"Step {step.id} succeeded: {step.result}")
            except Exception as e:
                step.status = "failed"
                step.result = f"Attempt {attempt} failed: {e}"
                logger.error(step.result)
            finally:
                # save DOM
                try:
                    dom = self.controller.run_js("document.documentElement.outerHTML")
                    filename = self.artifact_dir / f"dom_step_{step.id}_attempt_{attempt}.html"
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(dom)
                    step.dom_snapshot = str(filename)
                    logger.info(
                        f"Saved DOM snapshot for step {step.id} attempt {attempt}: {filename}"
                    )
                except Exception as dom_exc:
                    logger.warning(f"Failed to save DOM for step {step.id}: {dom_exc}")

        return step


# ─── Main Orchestration ────────────────────────────────────────────────────────
def main():
    plan_file = DATA_DIR / "plan.json"
    manager = PlanManager(str(plan_file))
    exec_logger = ExecutionLogger()
    memory = MemoryModule()

    try:
        plan = manager.load()
    except FileNotFoundError:
        llm = OpenAI(api_key="YOUR_KEY")
        planner = Planner(llm)
        plan = planner.generate_plan("Merge pull request")
        manager.save(plan)

    executor = StepExecutor(artifact_dir=str(DATA_DIR))

    for step in plan.steps:
        if step.status == "pending":
            manager.backup()
            updated = executor.execute(step)
            manager.save(plan)

            # structured log event
            event = {
                "timestamp": datetime.now().isoformat(),
                "step_id": step.id,
                "description": step.description or step.type,
                "status": step.status,
                "result": step.result,
                "dom_snapshot": step.dom_snapshot,
            }
            exec_logger.log_event(event)
            memory.record_event(event)

            if updated.status != "success":
                action = input(
                    f"Step {step.id} failed. Choose: [r]ollback, [a]bandon, [c]ontinue, or [q]uit: "
                )
                cmd = action.strip().lower()
                if cmd.startswith("r"):
                    num = input("Rollback to step #: ")
                    if num.isdigit():
                        plan = manager.restore(int(num))
                    continue
                elif cmd.startswith("a"):
                    updated.status = "abandoned"
                    updated.result = "abandoned by user"
                    manager.save(plan)
                    logger.info(f"Step {step.id} abandoned by user")
                    continue
                elif cmd.startswith("q"):
                    logger.info("User quit execution loop")
                    return
                else:
                    plan = manager.load()

    logger.info("All steps complete!")
    print("All steps complete!")


if __name__ == "__main__":
    main()
