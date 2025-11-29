import time
import requests
import pandas as pd
from datetime import datetime

# --- KONFIGURACJA ---
SUBREDDITS = ["Polska", "europe", "worldnews", "politics", "ukraine"]
FETCH_INTERVAL = 60     # sekundy między pobraniami (1 min)
MAX_POSTS = 500         # maksymalna liczba postów do zebrania
OUTPUT_FILE = "reddit_stream_topics.csv"

# --- FUNKCJA POBIERAJĄCA NAJNOWSZE POSTY ---
def fetch_new_posts(subreddit, limit=10):
    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
    headers = {"User-Agent": "reddit-stream-analysis-bot/0.1 by student"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            print(f"Błąd {r.status_code} dla {subreddit}")
            return []
        data = r.json()["data"]["children"]
        posts = []
        for d in data:
            post = d["data"]
            posts.append({
                "subreddit": subreddit,
                "id": post["id"],
                "title": post["title"],
                "author": post.get("author"),
                "created_utc": datetime.utcfromtimestamp(post["created_utc"]),
                "score": post["score"],
                "num_comments": post["num_comments"],
                "url": "https://reddit.com" + post["permalink"],
            })
        return posts
    except Exception as e:
        print(f"Błąd pobierania z {subreddit}: {e}")
        return []

# --- GŁÓWNA PĘTLA STRUMIENIA ---
def stream_subreddits():
    all_posts = {}
    print("Startuję strumień Reddita (Polska, polityka, wojna, świat)...")
    while len(all_posts) < MAX_POSTS:
        new_batch = []
        for sub in SUBREDDITS:
            posts = fetch_new_posts(sub, limit=10)
            for post in posts:
                if post["id"] not in all_posts:
                    all_posts[post["id"]] = post
                    new_batch.append(post)
        if new_batch:
            print(f"[{datetime.now()}] Dodano {len(new_batch)} nowych postów.")
            df = pd.DataFrame(new_batch)
            df.to_csv(OUTPUT_FILE, mode='a', header=not bool(len(all_posts) - len(new_batch)), index=False)
        else:
            print(f"[{datetime.now()}] Brak nowych postów.")
        time.sleep(FETCH_INTERVAL)
    print(f"Zebrano {len(all_posts)} postów. Dane zapisano w {OUTPUT_FILE}")

# --- URUCHOMIENIE ---
if __name__ == "__main__":
    stream_subreddits()
