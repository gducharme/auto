from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from openai import OpenAI
from ..utils.periodic import PeriodicWorker

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


class Supervisor:
    """Monitor automation progress and trigger replanning when needed."""

    def __init__(self) -> None:
        self.pm = PlanManager("plan.json")
        self.el = ExecutionLogger("execution_log.json")
        self.mm = MemoryModule("memory.json")
        self.rp = RetroPlanner(llm_client=OpenAI(), log_store=self.el, pm=self.pm)
        self._last_check = datetime.min.replace(tzinfo=timezone.utc)
        self._worker = PeriodicWorker(self._step, 1)

    async def _step(self) -> None:
        now = datetime.now(timezone.utc)
        if now - self._last_check < CHECK_INTERVAL:
            return
        self._last_check = now

        plan = self.pm.load()
        events = self.el.events
        last_event = events[-1] if events else None

        # 1) Time-based stall
        if last_event and (
            now - datetime.fromisoformat(last_event["timestamp"]) > MAX_STALL
        ):
            reason = "stall detected"
        # 2) Failure-based trigger
        elif (
            self.mm.memory["step_stats"].get(str(plan.steps[0].id), {}).get("failed", 0)
            >= MAX_FAILURES
        ):
            reason = "too many failures"
        else:
            reason = None

        if reason:
            logger.info("[Supervisor] Triggering replan: %s", reason)
            self.rp.replan(plan)

    async def start(self) -> asyncio.Task | None:
        return await self._worker.start()

    async def stop(self) -> None:
        await self._worker.stop()


async def supervise_loop() -> None:
    supervisor = Supervisor()
    await supervisor.start()
    try:
        if supervisor._worker.task:
            await supervisor._worker.task
    finally:
        await supervisor.stop()
