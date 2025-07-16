import asyncio
import logging
from typing import Optional

from .feeds.ingestion import run_ingest_async
from .config import get_ingest_interval

logger = logging.getLogger(__name__)


async def _ingest_loop():
    while True:
        try:
            await run_ingest_async()
        except Exception as exc:
            logger.error("Scheduled ingestion failed: %s", exc)
        await asyncio.sleep(get_ingest_interval())


class IngestScheduler:
    """Run feed ingestion on a timer in the background."""

    def __init__(self) -> None:
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> Optional[asyncio.Task]:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(_ingest_loop())
        return self._task

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None


# backward compatible default instance
default_scheduler = IngestScheduler()


async def start() -> Optional[asyncio.Task]:
    return await default_scheduler.start()


async def stop() -> None:
    await default_scheduler.stop()
