from fastapi import Depends, FastAPI, HTTPException

from app.core.config import Settings, get_settings
from app.models.schemas import RedditPost
from app.services.queue import get_queue
from app.services.reports import aggregate
from app.services.storage import storage


def get_app_settings() -> Settings:
    return get_settings()


app = FastAPI(
    title="Poland Safety Stream",
    version="0.1.0",
    summary="Streams Reddit posts, classifies war-related sentiment, and surfaces alerts.",
)


@app.get("/health")
def health(settings: Settings = Depends(get_app_settings)) -> dict:
    return {"status": "ok", "redis_stream": settings.redis_stream}


@app.post("/ingest/reddit")
def ingest_post(post: RedditPost):
    queue = get_queue()
    queue.publish(post.model_dump())
    storage.upsert_post(post.model_dump())
    return {"status": "queued", "id": post.id}


@app.get("/alerts")
def list_alerts(limit: int = 50):
    return storage.get_alerts(limit=limit)


@app.get("/reports/{window}")
def report(window: str = "daily"):
    if window not in {"daily", "weekly", "monthly"}:
        raise HTTPException(status_code=400, detail="window must be daily|weekly|monthly")
    return aggregate(window)
