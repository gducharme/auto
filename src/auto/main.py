# main.py
from fastapi import FastAPI, HTTPException
import asyncio
from contextlib import asynccontextmanager
from .feeds.ingestion import init_db, run_ingest
from .scheduler import Scheduler
from . import configure_logging
from .metrics import router as metrics_router
from .web_posts import router as posts_router
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    init_db()
    sched = Scheduler()
    await sched.start()
    try:
        yield
    finally:
        await sched.stop()


app = FastAPI(lifespan=lifespan)
app.include_router(metrics_router)
app.include_router(posts_router)


@app.post("/ingest")
async def ingest():
    logger.info("Ingestion requested")
    try:
        await asyncio.to_thread(run_ingest)
    except Exception:
        raise HTTPException(status_code=500, detail="ingestion failed")
    return {"status": "ingestion complete"}
