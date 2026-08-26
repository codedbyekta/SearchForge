from app.crawler.parser import ParsedDocument
from app.search.inverted_index import InvertedIndex
from app.services import indexing_service


def _sample_parsed(text="search engines index documents", content_hash="abc123"):
    return ParsedDocument(title="Sample", text=text, headings=[], links=[], content_hash=content_hash)


def test_index_parsed_document_creates_document(db_session, monkeypatch):
    fresh_index = InvertedIndex()
    monkeypatch.setattr(indexing_service, "get_index", lambda: fresh_index)
    monkeypatch.setattr(indexing_service, "persist_index", lambda: None)

    doc, was_indexed = indexing_service.index_parsed_document(
        db_session, url="https://example.com/a", canonical_url="https://example.com/a", parsed=_sample_parsed()
    )

    assert was_indexed is True
    assert doc.canonical_url == "https://example.com/a"
    assert fresh_index.total_docs == 1


def test_index_parsed_document_skips_unchanged_content(db_session, monkeypatch):
    fresh_index = InvertedIndex()
    monkeypatch.setattr(indexing_service, "get_index", lambda: fresh_index)
    monkeypatch.setattr(indexing_service, "persist_index", lambda: None)

    parsed = _sample_parsed(content_hash="same-hash")
    indexing_service.index_parsed_document(
        db_session, url="https://example.com/a", canonical_url="https://example.com/a", parsed=parsed
    )
    doc2, was_indexed2 = indexing_service.index_parsed_document(
        db_session, url="https://example.com/a", canonical_url="https://example.com/a", parsed=parsed
    )

    assert was_indexed2 is False
    assert fresh_index.total_docs == 1  # not double-indexed


def test_index_parsed_document_reindexes_changed_content(db_session, monkeypatch):
    fresh_index = InvertedIndex()
    monkeypatch.setattr(indexing_service, "get_index", lambda: fresh_index)
    monkeypatch.setattr(indexing_service, "persist_index", lambda: None)

    indexing_service.index_parsed_document(
        db_session,
        url="https://example.com/a",
        canonical_url="https://example.com/a",
        parsed=_sample_parsed(text="old content", content_hash="hash1"),
    )
    doc, was_indexed = indexing_service.index_parsed_document(
        db_session,
        url="https://example.com/a",
        canonical_url="https://example.com/a",
        parsed=_sample_parsed(text="new updated content", content_hash="hash2"),
    )

    assert was_indexed is True
    assert doc.content == "new updated content"
    assert fresh_index.total_docs == 1  # replaced, not duplicated
