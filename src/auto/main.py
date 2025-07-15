# main.py
from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
from .feeds.ingestion import init_db, fetch_feed, save_entries
from . import scheduler
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
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
