# main.py
from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
from .feeds.ingestion import init_db, run_ingest
from . import scheduler, configure_logging
from . import ingest_scheduler
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    init_db()
    await scheduler.start()
    await ingest_scheduler.start()
    try:
        yield
    finally:
        await scheduler.stop()
        await ingest_scheduler.stop()


app = FastAPI(lifespan=lifespan)


@app.post("/ingest")
async def ingest(background_tasks: BackgroundTasks):
    logger.info("Ingestion requested")
    background_tasks.add_task(run_ingest)
    return {"status": "ingestion queued"}
