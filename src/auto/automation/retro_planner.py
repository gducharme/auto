from __future__ import annotations

import logging
from openai import OpenAI

from ..plan.logging import ExecutionLogger
from ..plan.types import Plan, PlanManager, Step

logger = logging.getLogger(__name__)


class RetroPlanner:
    """Simple planner that can regenerate a plan using an LLM."""

    def __init__(self, llm_client: OpenAI, log_store: ExecutionLogger, pm: PlanManager) -> None:
        self.llm = llm_client
        self.log_store = log_store
        self.pm = pm

    def _build_prompt(self, plan: Plan) -> str:
        recent = "\n".join(
            f"{e['timestamp']}: {e['description']} -> {e['status']}"
            for e in self.log_store.events[-10:]
        )
        step_text = "\n".join(s.description for s in plan.steps)
        return (
            "The automation has stalled or failed.\n"
            f"Objective: {plan.objective}\n"
            "Current steps:\n" + step_text + "\n"
            "Recent events:\n" + recent + "\n"
            "Provide a revised numbered list of steps."\
        )

    def replan(self, plan: Plan) -> Plan:
        prompt = self._build_prompt(plan)
        try:
            response = self.llm.complete(prompt)
        except Exception as exc:
            logger.warning("LLM replanning failed: %s", exc)
            return plan

        lines = [line.strip() for line in response.splitlines() if line.strip()]
        new_steps = [Step(id=i, description=line) for i, line in enumerate(lines, 1)]
        new_plan = Plan(objective=plan.objective, steps=new_steps)
        self.pm.save(new_plan)
        logger.info("Generated revised plan with %d steps", len(new_steps))
        return new_plan
