import asyncio

import auto.ingest_scheduler as ingest_scheduler
import auto.main as main


def test_ingest_scheduler_runs(monkeypatch):
    called = {"count": 0}

    async def fake_run_ingest():
        called["count"] += 1

    monkeypatch.setattr(ingest_scheduler, "run_ingest_async", fake_run_ingest)
    monkeypatch.setenv("INGEST_INTERVAL", "0")

    scheduler = ingest_scheduler.IngestScheduler()

    async def run_loop():
        await scheduler.start()
        await asyncio.sleep(0.01)
        await scheduler.stop()

    asyncio.run(run_loop())
    assert called["count"] >= 1
