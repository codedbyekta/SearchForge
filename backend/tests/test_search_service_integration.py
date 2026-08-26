from app.crawler.parser import ParsedDocument
from app.search.inverted_index import InvertedIndex
from app.services import indexing_service, search_service


def _index_two_docs(db_session, monkeypatch):
    fresh_index = InvertedIndex()
    monkeypatch.setattr(indexing_service, "get_index", lambda: fresh_index)
    monkeypatch.setattr(indexing_service, "persist_index", lambda: None)
    monkeypatch.setattr(search_service, "get_index", lambda: fresh_index)

    indexing_service.index_parsed_document(
        db_session,
        url="https://example.com/a",
        canonical_url="https://example.com/a",
        parsed=ParsedDocument(title="Search Engines 101", text="search engines index documents", headings=[], links=[], content_hash="h1"),
    )
    indexing_service.index_parsed_document(
        db_session,
        url="https://example.com/b",
        canonical_url="https://example.com/b",
        parsed=ParsedDocument(title="Cooking Guide", text="recipes and cooking food", headings=[], links=[], content_hash="h2"),
    )
    return fresh_index


def test_search_returns_ranked_results(db_session, monkeypatch):
    monkeypatch.setattr(search_service, "cache_get", lambda key: None)
    monkeypatch.setattr(search_service, "cache_set", lambda key, value, ttl_seconds=None: True)

    _index_two_docs(db_session, monkeypatch)

    result = search_service.search(db_session, query="search engines", page=1, limit=10, mode="bm25")

    assert result["total"] == 1
    assert result["results"][0]["title"] == "Search Engines 101"
    assert result["query"] == "search engines"
    assert result["cached"] is False


def test_search_no_matching_terms_returns_empty(db_session, monkeypatch):
    monkeypatch.setattr(search_service, "cache_get", lambda key: None)
    monkeypatch.setattr(search_service, "cache_set", lambda key, value, ttl_seconds=None: True)

    _index_two_docs(db_session, monkeypatch)

    result = search_service.search(db_session, query="astrophysics", page=1, limit=10, mode="bm25")
    assert result["total"] == 0
    assert result["results"] == []


def test_search_uses_cache_when_present(db_session, monkeypatch):
    cached_payload = {
        "query": "cached query",
        "results": [],
        "total": 0,
        "page": 1,
        "limit": 10,
        "latency_ms": 1.0,
        "cached": False,
        "mode": "bm25",
    }
    monkeypatch.setattr(search_service, "cache_get", lambda key: dict(cached_payload))

    called = {"set": False}

    def fake_set(key, value, ttl_seconds=None):
        called["set"] = True
        return True

    monkeypatch.setattr(search_service, "cache_set", fake_set)

    result = search_service.search(db_session, query="cached query", page=1, limit=10, mode="bm25")
    assert result["cached"] is True
    assert called["set"] is False  # cache hit must not overwrite cache


def test_search_tfidf_mode(db_session, monkeypatch):
    monkeypatch.setattr(search_service, "cache_get", lambda key: None)
    monkeypatch.setattr(search_service, "cache_set", lambda key, value, ttl_seconds=None: True)

    _index_two_docs(db_session, monkeypatch)

    result = search_service.search(db_session, query="cooking", page=1, limit=10, mode="tfidf")
    assert result["mode"] == "tfidf"
    assert result["total"] == 1


def test_build_snippet_centers_on_match():
    content = "x" * 300 + " the quick brown fox jumps " + "y" * 300
    snippet = search_service._build_snippet(content, ["quick"])
    assert "quick" in snippet
    assert snippet.startswith("...")
