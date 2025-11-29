from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict

from app.services.storage import storage


def aggregate(window: str = "daily") -> Dict[str, object]:
    """Aggregate stats for the given window."""
    hours = {"daily": 24, "weekly": 24 * 7, "monthly": 24 * 30}.get(window, 24)
    analyses = storage.recent_analyses(window_hours=hours)
    topics = Counter([a["topic"] for a in analyses])
    tones = Counter([a["tone"] for a in analyses])
    risks = Counter([a["risk"] for a in analyses])
    by_subreddit = Counter([a["subreddit"] for a in analyses])
    timeline = defaultdict(int)
    for a in analyses:
        dt = datetime.fromisoformat(a["processed_at"]).date().isoformat()
        timeline[dt] += 1
    return {
        "window_hours": hours,
        "counts": len(analyses),
        "topics": topics,
        "tones": tones,
        "risks": risks,
        "subreddits": by_subreddit,
        "timeline": timeline,
    }
