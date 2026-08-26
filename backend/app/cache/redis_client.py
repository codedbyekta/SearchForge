"""
Redis caching wrapper (PRD F9 / SRS: "Redis failure must not make search
unavailable"). Every method swallows connection errors and degrades to a
cache-miss rather than raising, so callers never need their own try/except.
"""
import json
from typing import Any, Optional

import redis

from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

_client: Optional[redis.Redis] = None
_disabled = False


def _get_client() -> Optional[redis.Redis]:
    global _client, _disabled
    if _disabled:
        return None
    if _client is None:
        try:
            _client = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1.0, socket_timeout=1.0)
            _client.ping()
        except redis.RedisError as exc:
            logger.warning("Redis unavailable, disabling cache: %s", exc)
            _disabled = True
            _client = None
    return _client


def cache_get(key: str) -> Optional[Any]:
    client = _get_client()
    if client is None:
        return None
    try:
        raw = client.get(key)
        return json.loads(raw) if raw else None
    except redis.RedisError as exc:
        logger.warning("Redis GET failed for %s: %s", key, exc)
        return None


def cache_set(key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
    client = _get_client()
    if client is None:
        return False
    try:
        client.set(key, json.dumps(value), ex=ttl_seconds or settings.CACHE_TTL_SECONDS)
        return True
    except redis.RedisError as exc:
        logger.warning("Redis SET failed for %s: %s", key, exc)
        return False


def cache_clear_prefix(prefix: str) -> int:
    """Delete all keys under a prefix. Used after index rebuilds."""
    client = _get_client()
    if client is None:
        return 0
    try:
        deleted = 0
        for key in client.scan_iter(match=f"{prefix}*"):
            client.delete(key)
            deleted += 1
        return deleted
    except redis.RedisError as exc:
        logger.warning("Redis prefix clear failed for %s: %s", prefix, exc)
        return 0


def make_search_cache_key(query: str, page: int, limit: int, mode: str) -> str:
    normalized_query = " ".join(query.strip().lower().split())
    return f"search:{mode}:{normalized_query}:p{page}:l{limit}"
