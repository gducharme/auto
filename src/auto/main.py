# main.py
from fastapi import FastAPI, BackgroundTasks
from contextlib import asynccontextmanager
from .feeds.ingestion import init_db, fetch_feed, save_entries
from dotenv import load_dotenv
import logging
import os

load_dotenv()
logger = logging.getLogger(__name__)

FEED_URL = os.getenv("SUBSTACK_FEED_URL")
DB_URL   = os.getenv("DATABASE_URL")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

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

