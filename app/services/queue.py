from __future__ import annotations

import json
from collections import deque
from typing import Any, Deque, Dict, List, Tuple

from app.core.config import get_settings

_QUEUE: BaseQueue | None = None

try:
    import redis  # type: ignore
    from redis.exceptions import ConnectionError as RedisConnectionError  # type: ignore
except ImportError:
    redis = None
    RedisConnectionError = Exception


class BaseQueue:
    def publish(self, payload: Dict[str, Any]) -> None:
        raise NotImplementedError

    def consume(self, last_id: str = "0-0", count: int = 10):
        raise NotImplementedError


class RedisQueue(BaseQueue):
    """Redis Stream wrapper with graceful fallback when server goes away."""

    def __init__(self, url: str, stream: str, maxlen: int = 10000):
        if not redis:
            raise RuntimeError("redis package not installed")
        self.client = redis.Redis.from_url(url, decode_responses=True)
        self.stream = stream
        self.maxlen = maxlen
        self._fallback: BaseQueue = LocalQueue()
        self._warned = False

    def publish(self, payload: Dict[str, Any]) -> None:
        try:
            self.client.xadd(
                self.stream,
                {"data": json.dumps(payload)},
                maxlen=self.maxlen,
                approximate=True,
            )
        except RedisConnectionError:
            if not self._warned:
                print("Redis connection lost; using local queue temporarily.")
                self._warned = True
            self._fallback.publish(payload)

    def consume(self, last_id: str = "0-0", count: int = 10):
        try:
            return self.client.xread({self.stream: last_id}, count=count, block=1000)
        except RedisConnectionError:
            if not self._warned:
                print("Redis connection lost; consuming from local queue.")
                self._warned = True
            return self._fallback.consume(last_id, count)


class LocalQueue(BaseQueue):
    """In-process queue for environments without Redis."""

    def __init__(self) -> None:
        self.q: Deque[Dict[str, Any]] = deque()

    def publish(self, payload: Dict[str, Any]) -> None:
        self.q.append(payload)

    def consume(self, last_id: str = "0-0", count: int = 10):
        items: List[Tuple[str, List[Tuple[str, Dict[str, str]]]]] = []
        for _ in range(min(count, len(self.q))):
            item = self.q.popleft()
            items.append(("local", [("local", {"data": json.dumps(item)})]))
        return items


def get_queue() -> BaseQueue:
    global _QUEUE
    if _QUEUE:
        return _QUEUE

    cfg = get_settings()
    if redis:
        try:
            client = RedisQueue(cfg.redis_url, cfg.redis_stream, cfg.max_queue_length)
            # quick health check; raises if server unavailable
            client.client.ping()
            _QUEUE = client
            return _QUEUE
        except RedisConnectionError:
            print("Redis unavailable, falling back to in-process queue.")
        except Exception as exc:  # pragma: no cover
            print(f"Redis init failed ({exc}); falling back to local queue.")
    _QUEUE = LocalQueue()
    return _QUEUE
