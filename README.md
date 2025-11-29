## Poland Safety Stream

FastAPI + worker + Redis streaming pipeline that ingests Reddit posts, classifies war-related content (topics, tone, source, risk), persists results, and raises alerts for dangerous signals.

### Layout
- `app/main.py` – FastAPI service exposing ingest endpoint, alerts, and reports.
- `ingest/reddit_stream.py` – producer pulling from Reddit and pushing messages into the queue while archiving to CSV.
- `app/workers/processor.py` – worker that consumes the queue, classifies posts (Hugging Face if available, keyword fallback otherwise), persists analyses, and triggers alerts.
- `app/services/` – queue abstraction (Redis/local), classifier, alert logic, reporting, and SQLite storage.
- `reddit_stream_topics.csv` – original CSV preserved for local archive.

### Quickstart
1. `python -m venv venv && source venv/bin/activate`
2. `pip install -r requirements.txt`  (models download on first run)
3. Start services:
   - API: `uvicorn app.main:app --reload`
   - Worker: `python -m app.workers.processor`
   - Producer: `python -m ingest.reddit_stream`
4. Hit `POST /ingest/reddit` with a Reddit post payload to enqueue manually, `GET /alerts` for alerts, `GET /reports/daily|weekly|monthly` for aggregates.

Env vars: `REDIS_URL`, `REDIS_STREAM`, `DATABASE_URL`, `CLASSIFIER_MODEL`, `ZERO_SHOT_MODEL`, `CLASSIFIER_DEVICE`, `ALERT_THRESHOLD`.

### Notes
- Without Redis installed, the queue falls back to an in-process deque so the worker still functions locally.
- SQLite is used by default; you can point `DATABASE_URL` to PostgreSQL or a vector DB adapter if you add one.
- Classifier uses HF pipelines when available; otherwise, keyword heuristics keep processing alive offline.
