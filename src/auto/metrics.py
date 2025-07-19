from fastapi import APIRouter, Response
from prometheus_client import (
    Counter,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from .db import SessionLocal
from .models import Post

POSTS_PUBLISHED = Counter(
    "posts_published_total", "Total posts successfully published", ["network"]
)
POSTS_FAILED = Counter(
    "posts_failed_total", "Total posts that failed to publish", ["network"]
)
POSTS_COLLECTED = Gauge("posts_collected_total", "Total posts collected")

router = APIRouter()


@router.get("/metrics")
def metrics() -> Response:
    """Return Prometheus metrics."""
    with SessionLocal() as session:
        total = session.query(Post).count()
        POSTS_COLLECTED.set(total)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
