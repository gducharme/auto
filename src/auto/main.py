# main.py
from fastapi import FastAPI, HTTPException
import asyncio
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
async def ingest():
    logger.info("Ingestion requested")
    try:
        await asyncio.to_thread(run_ingest)
    except Exception:
        raise HTTPException(status_code=500, detail="ingestion failed")
    return {"status": "ingestion complete"}
