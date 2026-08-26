"""Statistics service (PRD F7, SRS FR-06)."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import CrawlURL, CrawlURLStatus, Document, DocumentStatus
from app.search.index_store import get_index


def get_stats(db: Session) -> dict:
    document_count = db.execute(
        select(func.count()).select_from(Document).where(Document.status == DocumentStatus.INDEXED)
    ).scalar_one()

    crawled_urls = db.execute(
        select(func.count()).select_from(CrawlURL).where(CrawlURL.status == CrawlURLStatus.FETCHED)
    ).scalar_one()

    failed_urls = db.execute(
        select(func.count()).select_from(CrawlURL).where(CrawlURL.status == CrawlURLStatus.FAILED)
    ).scalar_one()

    last_indexing_time = db.execute(select(func.max(Document.updated_at))).scalar_one()

    index = get_index()

    return {
        "document_count": document_count,
        "indexed_terms": index.term_count(),
        "crawled_urls": crawled_urls,
        "failed_urls": failed_urls,
        "last_indexing_time": last_indexing_time,
    }
