import json
import time
from typing import Any, Dict

from app.services.alerts import evaluate_alert
from app.services.classifier import PostClassifier
from app.services.queue import get_queue
from app.services.storage import storage


def _decode_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    raw = msg.get("data") or msg.get(b"data")
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    if isinstance(raw, str):
        return json.loads(raw)
    return raw or {}


def process_once(classifier: PostClassifier) -> bool:
    queue = get_queue()
    messages = queue.consume(count=25)
    if not messages:
        return False
    for _, stream_messages in messages:
        for msg_id, payload in stream_messages:
            data = _decode_message(payload)
            if not data:
                continue
            storage.upsert_post(data)
            analysis = classifier.classify(data.get("title", ""))
            storage.save_analysis(data["id"], analysis)
            evaluate_alert(data, analysis)
    return True


def main(loop: bool = True) -> None:
    classifier = PostClassifier()
    while True:
        has_data = process_once(classifier)
        if not loop:
            break
        if not has_data:
            time.sleep(1)


if __name__ == "__main__":
    main(loop=True)
