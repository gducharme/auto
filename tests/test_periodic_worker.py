import asyncio
from auto.utils.periodic import PeriodicWorker


def test_periodic_worker_runs_and_stops():
    counter = {"count": 0}

    async def work():
        counter["count"] += 1

    worker = PeriodicWorker(work, 0.01)

    async def run():
        await worker.start()
        await asyncio.sleep(0.03)
        await worker.stop()

    asyncio.run(run())

    assert worker.task is None
    assert counter["count"] >= 2
