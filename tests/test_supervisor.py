import asyncio
from datetime import datetime, timezone, timedelta

from auto.automation import supervisor


class DummyPlan:
    def __init__(self):
        self.objective = "test"
        self.steps = [type("Step", (), {"id": 1})()]


class DummyPlanManager:
    def load(self):
        return DummyPlan()


class DummyExecutionLogger:
    def __init__(self):
        self.events = []


class DummyMemoryModule:
    def __init__(self, failed=0):
        self.memory = {"step_stats": {"1": {"failed": failed}}}


class DummyRetroPlanner:
    def __init__(self):
        self.called = False

    def replan(self, plan):
        self.called = True
        return plan


def test_supervisor_start_stop(monkeypatch):
    pm = DummyPlanManager()
    el = DummyExecutionLogger()
    mm = DummyMemoryModule(failed=5)
    rp = DummyRetroPlanner()

    monkeypatch.setattr(supervisor, "PlanManager", lambda *a, **k: pm)
    monkeypatch.setattr(supervisor, "ExecutionLogger", lambda *a, **k: el)
    monkeypatch.setattr(supervisor, "MemoryModule", lambda *a, **k: mm)
    monkeypatch.setattr(supervisor, "RetroPlanner", lambda *a, **k: rp)
    monkeypatch.setattr(supervisor, "OpenAI", lambda *a, **k: object())

    sup = supervisor.Supervisor()
    sup._last_check = (
        datetime.now(timezone.utc) - supervisor.CHECK_INTERVAL - timedelta(seconds=1)
    )

    async def run():
        await sup.start()
        await asyncio.sleep(0.05)
        await sup.stop()

    asyncio.run(run())

    assert sup._worker.task is None
    assert rp.called
