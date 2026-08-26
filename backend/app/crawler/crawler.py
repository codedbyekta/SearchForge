"""
Crawler engine (PRD F1 / Development Plan Phase 5).

Synchronous-friendly, dependency-light BFS crawler:
  seed URL -> frontier queue -> fetch -> parse -> extract links -> enqueue
Respects robots.txt, page/depth limits, timeouts+retries, SSRF protection,
and per-job duplicate detection.
"""
import urllib.robotparser as robotparser
from dataclasses import dataclass, field
from typing import Callable, List, Optional
from urllib.parse import urlsplit

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.url_safety import URLSafetyError, validate_and_normalize_url
from app.crawler.parser import ParsedDocument, parse_html
from app.crawler.url_manager import URLFrontier, canonicalize_url

settings = get_settings()
logger = get_logger(__name__)


@dataclass
class CrawledPage:
    url: str
    canonical_url: str
    depth: int
    http_status: Optional[int]
    parsed: Optional[ParsedDocument]
    error: Optional[str] = None


@dataclass
class CrawlResult:
    pages: List[CrawledPage] = field(default_factory=list)
    pages_crawled: int = 0
    pages_failed: int = 0


class RobotsCache:
    """Caches robots.txt parsers per host for the duration of one crawl job."""

    def __init__(self, client: httpx.Client, user_agent: str) -> None:
        self._client = client
        self._user_agent = user_agent
        self._cache: dict[str, robotparser.RobotFileParser] = {}

    def can_fetch(self, url: str) -> bool:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._cache:
            rp = robotparser.RobotFileParser()
            try:
                resp = self._client.get(f"{origin}/robots.txt", timeout=settings.CRAWLER_TIMEOUT_SECONDS)
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
                else:
                    rp.parse([])  # no robots.txt -> allow everything
            except httpx.HTTPError:
                rp.parse([])  # fail-open on robots.txt fetch errors, but page fetch is still limited
            self._cache[origin] = rp
        return self._cache[origin].can_fetch(self._user_agent, url)


@retry(
    reraise=True,
    stop=stop_after_attempt(settings.CRAWLER_MAX_RETRIES + 1),
    wait=wait_exponential(multiplier=0.5, max=4),
    retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
)
def _fetch(client: httpx.Client, url: str) -> httpx.Response:
    return client.get(url, timeout=settings.CRAWLER_TIMEOUT_SECONDS, follow_redirects=True)


def crawl(
    seed_url: str,
    max_pages: int,
    max_depth: int,
    on_page: Optional[Callable[[CrawledPage], None]] = None,
) -> CrawlResult:
    """
    Run a synchronous BFS crawl starting at seed_url.

    `on_page` is invoked after each successfully-or-unsuccessfully fetched
    page, letting the caller persist incremental progress (used by the
    indexing service so a single failure doesn't lose already-crawled work).
    """
    max_pages = min(max_pages, settings.CRAWLER_MAX_PAGES_HARD_LIMIT)
    max_depth = min(max_depth, settings.CRAWLER_MAX_DEPTH_HARD_LIMIT)

    result = CrawlResult()
    frontier = URLFrontier()

    try:
        normalized_seed = validate_and_normalize_url(seed_url)
    except URLSafetyError as exc:
        result.pages.append(
            CrawledPage(url=seed_url, canonical_url=seed_url, depth=0, http_status=None, parsed=None, error=str(exc))
        )
        result.pages_failed += 1
        return result

    frontier.add(normalized_seed, 0)
    seed_origin = f"{urlsplit(normalized_seed).scheme}://{urlsplit(normalized_seed).netloc}"

    headers = {"User-Agent": settings.CRAWLER_USER_AGENT}
    with httpx.Client(headers=headers) as client:
        robots = RobotsCache(client, settings.CRAWLER_USER_AGENT)

        while frontier.has_next() and result.pages_crawled + result.pages_failed < max_pages:
            url, depth = frontier.next()

            page = _process_url(client, robots, url, depth)
            if page.error is None:
                result.pages_crawled += 1
            else:
                result.pages_failed += 1

            result.pages.append(page)
            if on_page:
                on_page(page)

            if page.parsed and depth < max_depth:
                for link in page.parsed.links:
                    try:
                        safe_link = validate_and_normalize_url(link, resolve_dns=False)
                    except URLSafetyError:
                        continue
                    # MVP scope: stay within the seed's origin to keep crawls bounded.
                    if not safe_link.startswith(seed_origin):
                        continue
                    frontier.add(safe_link, depth + 1)

    return result


def _process_url(client: httpx.Client, robots: RobotsCache, url: str, depth: int) -> CrawledPage:
    canonical = canonicalize_url(url)

    try:
        if not robots.can_fetch(url):
            return CrawledPage(url=url, canonical_url=canonical, depth=depth, http_status=None, parsed=None, error="Blocked by robots.txt")

        resp = _fetch(client, url)
        if resp.status_code >= 400:
            return CrawledPage(url=url, canonical_url=canonical, depth=depth, http_status=resp.status_code, parsed=None, error=f"HTTP {resp.status_code}")

        content_type = resp.headers.get("content-type", "")
        if "text/html" not in content_type:
            return CrawledPage(url=url, canonical_url=canonical, depth=depth, http_status=resp.status_code, parsed=None, error=f"Unsupported content-type: {content_type}")

        parsed = parse_html(resp.text, base_url=str(resp.url))
        return CrawledPage(url=url, canonical_url=canonical, depth=depth, http_status=resp.status_code, parsed=parsed, error=None)

    except (httpx.TransportError, httpx.TimeoutException) as exc:
        logger.warning("Fetch failed for %s: %s", url, exc)
        return CrawledPage(url=url, canonical_url=canonical, depth=depth, http_status=None, parsed=None, error=str(exc))
