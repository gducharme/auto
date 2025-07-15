# main.py
from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
from .feeds.ingestion import init_db, fetch_feed, save_entries
from . import scheduler, configure_logging
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    configure_logging()
    init_db()
    await scheduler.start()
    try:
        yield
    finally:
        await scheduler.stop()


app = FastAPI(lifespan=lifespan)


@app.post("/ingest")
async def ingest(background_tasks: BackgroundTasks):
    logger.info("Ingestion requested")
    background_tasks.add_task(run_ingest)
    return {"status": "ingestion queued"}


def run_ingest():
    try:
        items = fetch_feed()
        save_entries(items)
    except Exception as exc:
        logger.error("Ingestion failed: %s", exc)
