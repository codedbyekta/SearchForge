"""Search service (PRD F5/F6/F7, SRS FR-01/FR-02/FR-03)."""
import time
from typing import List, Literal, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.cache.redis_client import cache_get, cache_set, make_search_cache_key
from app.core.config import get_settings
from app.db.models import Document, SearchLog
from app.search import bm25, tfidf
from app.search.index_store import get_index
from app.search.tokenizer import tokenize

settings = get_settings()


class InvalidQueryError(ValueError):
    pass


def validate_query(query: str) -> str:
    if query is None or not query.strip():
        raise InvalidQueryError("Query must not be empty or whitespace-only")
    if len(query) > settings.MAX_QUERY_LENGTH:
        raise InvalidQueryError(f"Query exceeds maximum length of {settings.MAX_QUERY_LENGTH} characters")
    return query.strip()


def validate_pagination(page: int, limit: int) -> Tuple[int, int]:
    if page < 1:
        raise InvalidQueryError("page must be >= 1")
    if not (1 <= limit <= settings.MAX_PAGE_SIZE):
        raise InvalidQueryError(f"limit must be between 1 and {settings.MAX_PAGE_SIZE}")
    return page, limit


def _build_snippet(content: str, query_terms: List[str], width: int = 220) -> str:
    """Return a short window of content around the first matching query term."""
    lowered = content.lower()
    best_pos = -1
    for term in query_terms:
        pos = lowered.find(term)
        if pos != -1 and (best_pos == -1 or pos < best_pos):
            best_pos = pos
    if best_pos == -1:
        return content[:width].strip() + ("..." if len(content) > width else "")

    start = max(0, best_pos - width // 3)
    end = min(len(content), start + width)
    snippet = content[start:end].strip()
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(content) else ""
    return f"{prefix}{snippet}{suffix}"


def search(
    db: Session,
    query: str,
    page: int = 1,
    limit: int = 10,
    mode: Literal["tfidf", "bm25"] = "bm25",
) -> dict:
    start_time = time.perf_counter()

    query = validate_query(query)
    page, limit = validate_pagination(page, limit)

    cache_key = make_search_cache_key(query, page, limit, mode)
    cached = cache_get(cache_key)
    if cached is not None:
        cached["latency_ms"] = round((time.perf_counter() - start_time) * 1000, 2)
        cached["cached"] = True
        return cached

    query_terms = tokenize(query)
    index = get_index()

    ranker = bm25 if mode == "bm25" else tfidf
    ranked = ranker.rank(index, query_terms) if query_terms else []

    total = len(ranked)
    start = (page - 1) * limit
    end = start + limit
    page_slice = ranked[start:end]

    doc_ids = [doc_id for doc_id, _ in page_slice]
    documents_by_id = {}
    if doc_ids:
        rows = db.execute(select(Document).where(Document.id.in_(doc_ids))).scalars().all()
        documents_by_id = {row.id: row for row in rows}

    results = []
    for doc_id, score in page_slice:
        doc = documents_by_id.get(doc_id)
        if not doc:
            continue
        results.append(
            {
                "id": doc.id,
                "title": doc.title or doc.url,
                "url": doc.url,
                "snippet": _build_snippet(doc.content, query_terms),
                "score": round(score, 4),
            }
        )

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    response = {
        "query": query,
        "results": results,
        "total": total,
        "page": page,
        "limit": limit,
        "latency_ms": latency_ms,
        "cached": False,
        "mode": mode,
    }

    cache_set(cache_key, response)

    try:
        db.add(SearchLog(query=query, result_count=total, latency_ms=latency_ms))
        db.commit()
    except Exception:
        db.rollback()  # search logging must never break the search response

    return response
