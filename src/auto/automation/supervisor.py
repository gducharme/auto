from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone

from openai import OpenAI

from .plan_executor import (
    ExecutionLogger,
    MemoryModule,
    PlanManager,
)
from .retro_planner import RetroPlanner

logger = logging.getLogger(__name__)

# Supervisory timing constants
CHECK_INTERVAL = timedelta(minutes=5)
MAX_STALL = timedelta(minutes=2)
MAX_FAILURES = 3


def supervise_loop() -> None:
    """Monitor automation progress and trigger replanning when needed."""
    pm = PlanManager()
    el = ExecutionLogger()
    mm = MemoryModule()
    rp = RetroPlanner(llm_client=OpenAI(), log_store=el, pm=pm)

    last_check = datetime.min.replace(tzinfo=timezone.utc)

    while True:
        now = datetime.now(timezone.utc)
        if now - last_check < CHECK_INTERVAL:
            time.sleep(30)
            continue
        last_check = now

        plan = pm.load()
        events = el.events
        last_event = events[-1] if events else None

        # 1) Time-based stall
        if last_event and (
            now - datetime.fromisoformat(last_event["timestamp"]) > MAX_STALL
        ):
            reason = "stall detected"
        # 2) Failure-based trigger
        elif (
            mm.memory["step_stats"].get(str(plan.steps[0].id), {}).get("failed", 0)
            >= MAX_FAILURES
        ):
            reason = "too many failures"
        else:
            reason = None

        if reason:
            logger.info("[Supervisor] Triggering replan: %s", reason)
            plan = rp.replan(plan)
        
        time.sleep(1)
