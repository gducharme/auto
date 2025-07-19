import asyncio
from typing import Any, Awaitable, Callable, Optional


class PeriodicWorker:
    """Run a callable repeatedly in an ``asyncio`` task."""

    def __init__(
        self,
        func: Callable[[], Awaitable[Any] | Any],
        interval: float | Callable[[], float],
    ) -> None:
        self._func = func
        self._interval = interval
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    @property
    def task(self) -> Optional[asyncio.Task]:
        """Return the underlying asyncio task if running."""
        return self._task

    async def _run(self) -> None:
        try:
            while not self._stop_event.is_set():
                if asyncio.iscoroutinefunction(self._func):
                    await self._func()
                else:
                    await asyncio.to_thread(self._func)
                wait = self._interval() if callable(self._interval) else self._interval
                await asyncio.sleep(wait)
        except asyncio.CancelledError:
            pass

    async def start(self) -> Optional[asyncio.Task]:
        if self._task is None or self._task.done():
            self._stop_event.clear()
            self._task = asyncio.create_task(self._run())
        return self._task

    async def stop(self) -> None:
        if self._task:
            self._stop_event.set()
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
