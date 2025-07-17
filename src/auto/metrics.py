from fastapi import APIRouter, Response
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

POSTS_PUBLISHED = Counter(
    "posts_published_total", "Total posts successfully published", ["network"]
)
POSTS_FAILED = Counter(
    "posts_failed_total", "Total posts that failed to publish", ["network"]
)

router = APIRouter()


@router.get("/metrics")
def metrics() -> Response:
    """Return Prometheus metrics."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
