"""
URL normalization and per-crawl-job dedup tracking (SRS 2.6 business rules:
"A URL cannot be crawled twice within one crawl job").
"""
from urllib.parse import urldefrag, urlsplit, urlunsplit

TRACKING_PARAM_PREFIXES = ("utm_", "fbclid", "gclid", "ref")


def canonicalize_url(url: str) -> str:
    """
    Normalize a URL for deduplication purposes:
    - strip fragment
    - lowercase scheme/host
    - drop common tracking query params
    - remove trailing slash (except root)
    """
    url, _frag = urldefrag(url)
    parts = urlsplit(url)

    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()

    path = parts.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")

    query_pairs = [
        pair
        for pair in parts.query.split("&")
        if pair and not any(pair.lower().startswith(p) for p in TRACKING_PARAM_PREFIXES)
    ]
    query = "&".join(sorted(query_pairs))

    return urlunsplit((scheme, netloc, path, query, ""))


class URLFrontier:
    """Simple BFS-style queue with per-job seen-set deduplication."""

    def __init__(self) -> None:
        self._queue: list[tuple[str, int]] = []  # (url, depth)
        self._seen: set[str] = set()

    def add(self, url: str, depth: int) -> bool:
        canonical = canonicalize_url(url)
        if canonical in self._seen:
            return False
        self._seen.add(canonical)
        self._queue.append((canonical, depth))
        return True

    def has_next(self) -> bool:
        return len(self._queue) > 0

    def next(self) -> tuple[str, int]:
        return self._queue.pop(0)

    def seen_count(self) -> int:
        return len(self._seen)
