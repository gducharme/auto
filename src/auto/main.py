# main.py
from fastapi import FastAPI, BackgroundTasks
from .feeds.ingestion import init_db, fetch_feed, save_entries
from dotenv import load_dotenv
import os

load_dotenv()

FEED_URL = os.getenv("SUBSTACK_FEED_URL")
DB_URL   = os.getenv("DATABASE_URL")

app = FastAPI()

@app.on_event("startup")
async def startup():
    init_db()

@app.post("/ingest")
async def ingest(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_ingest)
    return {"status": "ingestion queued"}

def run_ingest():
    items = fetch_feed()
    save_entries(items)

