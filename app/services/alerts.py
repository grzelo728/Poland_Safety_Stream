from typing import Dict

from app.core.config import get_settings
from app.services.storage import storage


def evaluate_alert(post: Dict[str, str], analysis: Dict[str, str]) -> None:
    """Persist alert if risk or tone crosses thresholds."""
    cfg = get_settings()
    sentiment_score = analysis.get("sentiment_score", 0) or 0
    risk = analysis.get("risk", "low")
    tone = analysis.get("tone", "neutral")
    reasons = []
    if risk == "high":
        reasons.append("High-risk topic or wording")
    if sentiment_score < -cfg.alert_threshold:
        reasons.append("Strongly negative sentiment")
    if tone == "panic":
        reasons.append("Panic tone detected")
    if reasons:
        storage.add_alert(
            post_id=post["id"],
            risk=risk,
            reason="; ".join(reasons),
        )
