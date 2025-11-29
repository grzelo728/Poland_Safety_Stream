import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import pandas as pd
import requests

from app.services.queue import get_queue

SUBREDDITS = ["Polska", "europe", "worldnews", "politics", "ukraine"]
FETCH_INTERVAL = 60  # seconds
MAX_POSTS = 500
OUTPUT_FILE = Path("reddit_stream_topics.csv")


def fetch_new_posts(subreddit: str, limit: int = 10) -> List[Dict[str, object]]:
    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
    headers = {"User-Agent": "reddit-stream-analysis-bot/0.2 by student"}
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    data = r.json()["data"]["children"]
    posts = []
    for d in data:
        post = d["data"]
        posts.append(
            {
                "subreddit": subreddit,
                "id": post["id"],
                "title": post["title"],
                "author": post.get("author"),
                "created_utc": datetime.fromtimestamp(
                    post["created_utc"], tz=timezone.utc
                ).isoformat(),
                "score": post["score"],
                "num_comments": post["num_comments"],
                "url": "https://reddit.com" + post["permalink"],
            }
        )
    return posts


def stream() -> None:
    queue = get_queue()
    seen = set()
    print("Starting Reddit stream...")
    while len(seen) < MAX_POSTS:
        new_batch: List[Dict[str, object]] = []
        for sub in SUBREDDITS:
            try:
                for post in fetch_new_posts(sub, limit=10):
                    if post["id"] in seen:
                        continue
                    seen.add(post["id"])
                    new_batch.append(post)
                    queue.publish(post)
            except Exception as exc:
                print(f"Fetch error for {sub}: {exc}")
        if new_batch:
            print(f"[{datetime.now()}] queued {len(new_batch)} posts")
            df = pd.DataFrame(new_batch)
            df.to_csv(
                OUTPUT_FILE,
                mode="a",
                header=not OUTPUT_FILE.exists(),
                index=False,
            )
        else:
            print(f"[{datetime.now()}] no new posts")
        time.sleep(FETCH_INTERVAL)
    print(f"Collected {len(seen)} posts. Data saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    stream()
