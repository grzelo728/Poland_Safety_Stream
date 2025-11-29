import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List


@dataclass
class Settings:
    """Centralized configuration loaded from environment variables."""

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_stream: str = os.getenv("REDIS_STREAM", "reddit:ingest")
    redis_group: str = os.getenv("REDIS_CONSUMER_GROUP", "workers")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
    classifier_model: str = os.getenv(
        "CLASSIFIER_MODEL", "cardiffnlp/twitter-roberta-base-sentiment-latest"
    )
    zero_shot_model: str = os.getenv(
        "ZERO_SHOT_MODEL", "facebook/bart-large-mnli"
    )
    classification_device: str = os.getenv("CLASSIFIER_DEVICE", "cpu")
    max_queue_length: int = int(os.getenv("MAX_QUEUE_LENGTH", "10000"))
    alert_threshold: float = float(os.getenv("ALERT_THRESHOLD", "0.80"))
    # category vocabularies used both for zero-shot and heuristics
    topics: List[str] = field(
        default_factory=lambda: [
            "war",
            "drones",
            "missiles",
            "border",
            "belarus",
            "ukraine",
            "poland",
            "propaganda",
        ]
    )
    emotional_tones: List[str] = field(
        default_factory=lambda: ["panic", "neutral", "chill"]
    )
    sources: List[str] = field(
        default_factory=lambda: ["victim", "media", "analysis", "meme"]
    )
    risks: List[str] = field(default_factory=lambda: ["high", "moderate", "low"])


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
