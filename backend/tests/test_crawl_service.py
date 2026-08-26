from app.crawler.crawler import CrawledPage, CrawlResult
from app.crawler.parser import ParsedDocument
from app.db.models import CrawlJobStatus
from app.services import crawl_service


def _fake_crawl_result():
    parsed = ParsedDocument(title="Page", text="hello world", headings=[], links=[], content_hash="h1")
    return CrawlResult(
        pages=[
            CrawledPage(url="https://example.com/", canonical_url="https://example.com/", depth=0, http_status=200, parsed=parsed),
        ],
        pages_crawled=1,
        pages_failed=0,
    )


def test_start_crawl_job_completes_successfully(db_session, monkeypatch):
    monkeypatch.setattr(crawl_service, "cache_clear_prefix", lambda prefix: 0)
    monkeypatch.setattr("app.services.indexing_service.persist_index", lambda: None)

    def fake_crawl(seed_url, max_pages, max_depth, on_page=None):
        result = _fake_crawl_result()
        if on_page:
            for page in result.pages:
                on_page(page)
        return result

    monkeypatch.setattr(crawl_service, "crawl", fake_crawl)

    job = crawl_service.start_crawl_job(db_session, "https://example.com/", max_pages=5, max_depth=1)

    assert job.status == CrawlJobStatus.COMPLETED
    assert job.pages_crawled == 1
    assert job.pages_failed == 0
    assert job.completed_at is not None


def test_start_crawl_job_rejects_unsafe_seed(db_session):
    import pytest

    from app.core.url_safety import URLSafetyError

    with pytest.raises(URLSafetyError):
        crawl_service.start_crawl_job(db_session, "http://127.0.0.1/", max_pages=5, max_depth=1)


def test_start_crawl_job_marks_failed_on_exception(db_session, monkeypatch):
    monkeypatch.setattr(crawl_service, "cache_clear_prefix", lambda prefix: 0)

    def broken_crawl(seed_url, max_pages, max_depth, on_page=None):
        raise RuntimeError("boom")

    monkeypatch.setattr(crawl_service, "crawl", broken_crawl)

    job = crawl_service.start_crawl_job(db_session, "https://example.com/", max_pages=5, max_depth=1)
    assert job.status == CrawlJobStatus.FAILED
