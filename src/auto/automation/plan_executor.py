import shutil
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pathlib import Path
import argparse
from .safari import SafariController
from openai import OpenAI  # pseudo-import for LLM planning

from ..plan.types import Plan, PlanManager, Step
from .fixtures import load_commands
from ..plan.logging import (
    configure_logging,
    ExecutionLogger,
    MemoryModule,
)

# ─── Logging Configuration ─────────────────────────────────────────────────────
logger = logging.getLogger(__name__)


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
        max_retries: int = 3,
        snapshot_dir: str | Path = ".",
        cassette_dir: Optional[str | Path] = None,
        fixtures_root: Optional[str | Path] = None,
    ) -> None:
        self.controller = controller or SafariController()
        self.max_retries = max_retries
        self.snapshot_dir = Path(snapshot_dir)
        self.cassette_dir = Path(cassette_dir) if cassette_dir else None
        if fixtures_root is None:
            fixtures_root = Path(__file__).resolve().parents[3] / "tests" / "fixtures"
        self.fixtures_root = Path(fixtures_root)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        if self.cassette_dir:
            self.cassette_dir.mkdir(parents=True, exist_ok=True)
        # simple in-memory variable store for discovery steps
        self.variables: Dict[str, Any] = {}

    def _render(self, template: str, vars: Optional[Dict[str, Any]] = None) -> str:
        """Render a template string using stored and step variables."""
        from jinja2 import Template

        context = {**self.variables}
        if vars:
            context.update(vars)
        try:
            tmpl = Template(template)
            return tmpl.render(**context)
        except Exception as e:
            logger.error(f"Template render failed for '{template}': {e}")
            return template

    def check_pre_conditions(self, step: Step) -> bool:
        for cond in step.pre_conditions:
            logger.info(f"Checking pre-condition '{cond}' for step {step.id}")
            try:
                result = self.controller.run_js(
                    f"document.querySelector('{cond}') ? '1' : '0'"
                )
                if result != "1":
                    raise RuntimeError("element not found")
            except Exception as e:
                logger.error(f"Pre-condition '{cond}' failed: {e}")
                return False
        return True

    def check_post_conditions(self, step: Step) -> bool:
        for cond in step.post_conditions:
            logger.info(f"Checking post-condition '{cond}' for step {step.id}")
            if cond.startswith("url_contains:"):
                expected = cond.split(":", 1)[1].strip()
                current_url = self.controller.run_js("window.location.href")
                if expected not in current_url:
                    logger.error(
                        f"Post-condition '{cond}' failed: URL does not contain {expected}"
                    )
                    return False
            else:
                try:
                    result = self.controller.run_js(
                        f"document.querySelector('{cond}') ? '1' : '0'"
                    )
                    if result != "1":
                        raise RuntimeError("element not found")
                except Exception as e:
                    logger.error(f"Post-condition '{cond}' failed: {e}")
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
                    url = self._render(step.url, step.vars)
                    self.controller.open(url)
                    step.result = f"navigated to {url}"
                elif step.type == "click" and step.selector:
                    selector = self._render(step.selector, step.vars)
                    self.controller.click(selector)
                    step.result = f"clicked {selector}"
                elif step.type == "discover" and step.prompt_template:
                    # Real implementation would call an LLM with DOM and the prompt
                    dom = self.controller.run_js("document.documentElement.outerHTML")
                    rendered = self._render(step.prompt_template, step.vars)
                    logger.debug(f"Discovery prompt: {rendered[:100]}")
                    # Placeholder: store empty list
                    selectors: List[str] = []
                    if step.store_as:
                        self.variables[step.store_as] = selectors
                    step.result = f"discovered {len(selectors)} selectors"
                elif step.type == "run_fixture" and step.fixture:
                    vars_combined = {**self.variables, **(step.vars or {})}
                    commands = load_commands(
                        step.fixture, variables=vars_combined, root=self.fixtures_root
                    )
                    for cmd_entry in commands:
                        cmd = cmd_entry[0]
                        args = cmd_entry[1:]
                        if cmd == "open" and args:
                            self.controller.open(args[0])
                        elif cmd == "click" and args:
                            self.controller.click(args[0])
                        elif cmd == "fill" and len(args) == 2:
                            self.controller.fill(args[0], args[1])
                        elif cmd == "run_js" and args:
                            self.controller.run_js(args[0])
                        elif cmd == "close_tab":
                            self.controller.close_tab()
                    step.result = f"ran fixture {step.fixture}"
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
                    filename = f"dom_step_{step.id}_attempt_{attempt}.html"
                    path = self.snapshot_dir / filename
                    with path.open("w", encoding="utf-8") as f:
                        f.write(dom)
                    step.dom_snapshot = str(path)
                    logger.info(
                        f"Saved DOM snapshot for step {step.id} attempt {attempt}: {path}"
                    )
                    if self.cassette_dir:
                        dest = self.cassette_dir / filename
                        shutil.copy(path, dest)
                        logger.info(
                            f"Copied DOM snapshot for step {step.id} to cassette: {dest}"
                        )
                except Exception as dom_exc:
                    logger.warning(f"Failed to save DOM for step {step.id}: {dom_exc}")

        return step


# ─── Main Orchestration ────────────────────────────────────────────────────────
def main():
    configure_logging()
    parser = argparse.ArgumentParser(description="Execute or manage a plan")
    parser.add_argument("plan", nargs="?", default="plan.json", help="Source plan file")
    parser.add_argument(
        "--reset", action="store_true", help="Remove working plan and artifacts"
    )
    args = parser.parse_args()

    manager = PlanManager(args.plan)

    if args.reset:
        manager.reset()
        return
    exec_logger = ExecutionLogger()
    memory = MemoryModule()

    try:
        plan = manager.load()
    except FileNotFoundError:
        llm = OpenAI(api_key="YOUR_KEY")
        planner = Planner(llm)
        plan = planner.generate_plan("Merge pull request")
        manager.save(plan)

    plan_dir = Path(manager.path).resolve().parent
    cassette_dir = plan_dir / "cassettes"
    executor = StepExecutor(snapshot_dir=plan_dir, cassette_dir=cassette_dir)

    for step in plan.steps:
        if step.status == "pending":
            manager.backup()
            updated = executor.execute(step)
            manager.save(plan)

            # structured log event
            event = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
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
