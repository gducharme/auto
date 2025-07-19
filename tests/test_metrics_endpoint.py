import auto.main as main
from auto.metrics import POSTS_PUBLISHED, POSTS_COLLECTED
from auto.db import SessionLocal
from auto.models import Post
from fastapi.testclient import TestClient


def test_metrics_endpoint(test_db_engine):
    with SessionLocal() as session:
        session.add(Post(id="1", title="t1", link="http://1"))
        session.add(Post(id="2", title="t2", link="http://2"))
        session.commit()

    POSTS_PUBLISHED.labels(network="mastodon").inc()
    with TestClient(main.app) as client:
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "posts_published_total" in resp.text
    assert POSTS_COLLECTED._value.get() == 2
