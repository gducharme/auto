from pathlib import Path
from bs4 import BeautifulSoup
from auto.db import SessionLocal
from auto.models import Post
from auto.feeds import ingestion


def test_ingest_backfills_existing_posts(test_db_engine):
    items = BeautifulSoup(
        Path(__file__).with_name("sample_feed.xml").read_bytes(), "xml"
    ).find_all("item")

    with SessionLocal() as session:
        for it in items:
            guid = it.find("guid").text
            session.add(
                Post(id=guid, title=f"t{guid}", link=f"http://{guid}", summary="", published="")
            )
        session.commit()

    ingestion.save_entries(items)

    with SessionLocal() as session:
        posts = session.query(Post).order_by(Post.id).all()
        assert all(p.content for p in posts)
