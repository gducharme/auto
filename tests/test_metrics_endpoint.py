import auto.main as main
from auto.metrics import POSTS_PUBLISHED
from fastapi.testclient import TestClient


def test_metrics_endpoint():
    POSTS_PUBLISHED.labels(network="mastodon").inc()
    with TestClient(main.app) as client:
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "posts_published_total" in resp.text
