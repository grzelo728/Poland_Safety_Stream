from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class RedditPost(BaseModel):
    subreddit: str
    id: str
    title: str
    author: Optional[str] = None
    created_utc: datetime
    score: int = 0
    num_comments: int = 0
    url: Optional[str] = None


class AnalysisResult(BaseModel):
    post_id: str
    topic: str
    tone: str
    source: str
    risk: str
    sentiment_score: float
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    raw: Dict[str, Any] = Field(default_factory=dict)


class Alert(BaseModel):
    post_id: str
    risk: str
    reason: str
    created_at: datetime
    title: Optional[str]
    subreddit: Optional[str]
    url: Optional[str]
