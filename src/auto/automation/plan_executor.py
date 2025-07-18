import json
import shutil
import subprocess
import logging
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict
from datetime import datetime
from selenium import webdriver  # or playwright, etc.
from openai import OpenAI  # pseudo-import for LLM planning

# ─── Logging Configuration ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filename="agent.log",
    filemode="a",
)
logger = logging.getLogger(__name__)


# ─── Data Structures ───────────────────────────────────────────────────────────
@dataclass
class Step:
    id: int
    description: str
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
    def __init__(self, path: str = "execution_log.json"):
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
    def __init__(self, path: str = "memory.json"):
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
    def __init__(self, path: str, backup_dir: str = "backups"):
        self.path = path
        self.backup_dir = backup_dir

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
    def __init__(self, max_retries: int = 3):
        self.driver = webdriver.Chrome()
        self.max_retries = max_retries

    def check_pre_conditions(self, step: Step) -> bool:
        for cond in step.pre_conditions:
            logger.info(f"Checking pre-condition '{cond}' for step {step.id}")
            try:
                self.driver.find_element_by_css_selector(cond)
            except Exception as e:
                logger.error(f"Pre-condition '{cond}' failed: {e}")
                return False
        return True

    def check_post_conditions(self, step: Step) -> bool:
        for cond in step.post_conditions:
            logger.info(f"Checking post-condition '{cond}' for step {step.id}")
            if cond.startswith("url_contains:"):
                expected = cond.split(":", 1)[1].strip()
                if expected not in self.driver.current_url:
                    logger.error(
                        f"Post-condition '{cond}' failed: URL does not contain {expected}"
                    )
                    return False
            else:
                try:
                    self.driver.find_element_by_css_selector(cond)
                except Exception as e:
                    logger.error(f"Post-condition '{cond}' failed: {e}")
                    return False
        return True

    def execute(self, step: Step) -> Step:
        logger.info(f"Starting Step {step.id}: {step.description}")

        if step.pre_conditions and not self.check_pre_conditions(step):
            step.status = "failed"
            step.result = "pre-condition check failed"
            return step

        attempt = 0
        while attempt < self.max_retries and step.status == "pending":
            attempt += 1
            try:
                desc = step.description.lower()
                if "navigate to" in desc:
                    url = desc.split("navigate to", 1)[1].strip()
                    self.driver.get(url)
                    step.result = f"navigated to {url}"
                elif "click" in desc:
                    selector = desc.split("click", 1)[1].strip()
                    elem = self.driver.find_element_by_css_selector(selector)
                    elem.click()
                    step.result = f"clicked {selector}"
                else:
                    step.status = "failed"
                    step.result = "requires human input"
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
                    dom = self.driver.page_source
                    filename = f"dom_step_{step.id}_attempt_{attempt}.html"
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(dom)
                    step.dom_snapshot = filename
                    logger.info(
                        f"Saved DOM snapshot for step {step.id} attempt {attempt}: {filename}"
                    )
                except Exception as dom_exc:
                    logger.warning(f"Failed to save DOM for step {step.id}: {dom_exc}")

        return step


# ─── Main Orchestration ────────────────────────────────────────────────────────
def main():
    plan_file = "plan.json"
    manager = PlanManager(plan_file)
    exec_logger = ExecutionLogger()
    memory = MemoryModule()

    try:
        plan = manager.load()
    except FileNotFoundError:
        llm = OpenAI(api_key="YOUR_KEY")
        planner = Planner(llm)
        plan = planner.generate_plan("Merge pull request")
        manager.save(plan)

    executor = StepExecutor()

    for step in plan.steps:
        if step.status == "pending":
            manager.backup()
            updated = executor.execute(step)
            manager.save(plan)

            # structured log event
            event = {
                "timestamp": datetime.now().isoformat(),
                "step_id": step.id,
                "description": step.description,
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
