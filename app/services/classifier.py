import re
from typing import Dict, List, Optional

from app.core.config import get_settings

try:
    from transformers import pipeline  # type: ignore
except ImportError:
    pipeline = None


KEYWORDS_TOPIC = {
    "drones": ["drone", "bayraktar", "uav"],
    "missiles": ["missile", "rakieta", "patriot", "kinzhal"],
    "border": ["granica", "border", "przejscie", "kolumna"],
    "belarus": ["belarus", "białoru", "lukashenko"],
    "ukraine": ["ukraine", "ukraina", "kyiv", "kijow"],
    "poland": ["poland", "polska", "warsaw", "warszawa"],
    "propaganda": ["propaganda", "fake", "dezinformacja", "troll"],
    "war": ["wojna", "war", "front", "atak", "ostrzał"],
}

KEYWORDS_TONE = {
    "panic": ["panic", "alarm", "help", "ratunku", "pilne"],
    "chill": ["meme", "lol", "śmieszne", "joke"],
}

KEYWORDS_SOURCE = {
    "victim": ["widziałem", "jestem", "moja rodzina", "byłem"],
    "media": ["tvp", "gazeta", "report", "media"],
    "analysis": ["analysis", "thread", "deep dive", "raport", "analiza"],
    "meme": ["meme", "śmieszne", "joke", "lol"],
}


class PostClassifier:
    """Wraps HF pipelines with a keyword fallback so code works without the model."""

    def __init__(self) -> None:
        cfg = get_settings()
        self.sentiment_pipe = None
        self.zero_shot_pipe = None
        if pipeline:
            try:
                self.sentiment_pipe = pipeline(
                    "sentiment-analysis",
                    model=cfg.classifier_model,
                    device=0 if cfg.classification_device == "cuda" else -1,
                )
                self.zero_shot_pipe = pipeline(
                    "zero-shot-classification",
                    model=cfg.zero_shot_model,
                    device=0 if cfg.classification_device == "cuda" else -1,
                )
            except Exception as exc:  # pragma: no cover
                print(f"Classifier pipeline init failed, using keyword fallback: {exc}")

    def classify(self, text: str) -> Dict[str, str]:
        clean_text = text or ""
        return {
            "topic": self._classify_topic(clean_text),
            "tone": self._classify_tone(clean_text),
            "source": self._classify_source(clean_text),
            "risk": self._estimate_risk(clean_text),
            "sentiment_score": self._sentiment(clean_text),
        }

    def _sentiment(self, text: str) -> float:
        if self.sentiment_pipe:
            result = self.sentiment_pipe(text[:512])[0]
            score = result.get("score", 0.0)
            return score if result.get("label", "").lower().startswith("positive") else -score
        # fallback heuristic
        positive = len(re.findall(r"pokój|peace|sukces|wygrana", text, flags=re.I))
        negative = len(re.findall(r"atak|wojna|alarm|zabity|zgin", text, flags=re.I))
        return (positive - negative) / (positive + negative + 1)

    def _classify_topic(self, text: str) -> str:
        cfg = get_settings()
        if self.zero_shot_pipe:
            result = self.zero_shot_pipe(text[:512], cfg.topics)
            return result["labels"][0]
        return self._keyword_match(text, KEYWORDS_TOPIC, default="war")

    def _classify_tone(self, text: str) -> str:
        cfg = get_settings()
        if self.zero_shot_pipe:
            result = self.zero_shot_pipe(text[:512], cfg.emotional_tones)
            return result["labels"][0]
        return self._keyword_match(text, KEYWORDS_TONE, default="neutral")

    def _classify_source(self, text: str) -> str:
        cfg = get_settings()
        if self.zero_shot_pipe:
            result = self.zero_shot_pipe(text[:512], cfg.sources)
            return result["labels"][0]
        return self._keyword_match(text, KEYWORDS_SOURCE, default="media")

    def _estimate_risk(self, text: str) -> str:
        text_lower = text.lower()
        if any(w in text_lower for w in ["atak", "explosion", "wybuch", "ostrzał", "missile"]):
            return "high"
        if any(w in text_lower for w in ["alert", "ostrzeżenie", "mobilizacja"]):
            return "moderate"
        return "low"

    @staticmethod
    def _keyword_match(text: str, vocab: Dict[str, List[str]], default: str) -> str:
        text_lower = text.lower()
        for label, keywords in vocab.items():
            if any(k.lower() in text_lower for k in keywords):
                return label
        return default
