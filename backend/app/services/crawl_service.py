"""Crawl orchestration service (PRD F1, Development Plan Phase 5/6)."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.cache.redis_client import cache_clear_prefix
from app.core.logging import get_logger
from app.core.url_safety import URLSafetyError, validate_and_normalize_url
from app.crawler.crawler import CrawledPage, crawl
from app.db.models import CrawlJob, CrawlJobStatus, CrawlURL, CrawlURLStatus
from app.services.indexing_service import index_parsed_document

logger = get_logger(__name__)


def start_crawl_job(db: Session, seed_url: str, max_pages: int, max_depth: int) -> CrawlJob:
    # Fail fast on an obviously unsafe/invalid seed before creating a job row.
    validate_and_normalize_url(seed_url)  # raises URLSafetyError if invalid

    job = CrawlJob(
        seed_url=seed_url,
        max_pages=max_pages,
        max_depth=max_depth,
        status=CrawlJobStatus.RUNNING,
        started_at=datetime.now(timezone.utc),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        _run_crawl(db, job)
        job.status = CrawlJobStatus.COMPLETED
    except Exception as exc:  # a single unexpected failure must not corrupt job state
        logger.exception("Crawl job %s failed: %s", job.id, exc)
        job.status = CrawlJobStatus.FAILED
    finally:
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)

    # Any freshly indexed content invalidates previously cached search results.
    cache_clear_prefix("search:")

    return job


def _run_crawl(db: Session, job: CrawlJob) -> None:
    def on_page(page: CrawledPage) -> None:
        _persist_crawl_url(db, job, page)
        if page.parsed is not None:
            try:
                index_parsed_document(db, url=page.url, canonical_url=page.canonical_url, parsed=page.parsed)
            except Exception as exc:
                # A single failed indexing operation must not stop the crawl.
                logger.warning("Indexing failed for %s: %s", page.url, exc)
                job.pages_failed += 1
                job.pages_crawled = max(0, job.pages_crawled - 1)
        db.commit()

    result = crawl(job.seed_url, job.max_pages, job.max_depth, on_page=on_page)
    job.pages_crawled = result.pages_crawled
    job.pages_failed = result.pages_failed


def _persist_crawl_url(db: Session, job: CrawlJob, page: CrawledPage) -> None:
    status = CrawlURLStatus.FETCHED if page.error is None else CrawlURLStatus.FAILED
    entry = CrawlURL(
        crawl_job_id=job.id,
        url=page.url,
        depth=page.depth,
        status=status,
        http_status=page.http_status,
        error=page.error,
    )
    db.add(entry)
