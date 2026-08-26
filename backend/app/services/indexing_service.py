"""
Indexing pipeline (PRD F3/F4, Development Plan Phase 6): parser output ->
tokenizer -> inverted index, plus PostgreSQL metadata persistence.

Enforces SRS 2.6: "a document cannot be indexed twice under the same
canonical URL/version" — re-crawls of an unchanged page (same content_hash)
are skipped; changed content triggers re-indexing (old postings replaced).
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crawler.parser import ParsedDocument
from app.db.models import Document, DocumentStatus
from app.search.index_store import get_index, persist_index
from app.search.tokenizer import tokenize, word_count


def index_parsed_document(
    db: Session, url: str, canonical_url: str, parsed: ParsedDocument
) -> tuple[Document, bool]:
    """
    Upsert a Document row and (re)index it. Returns (document, was_indexed).

    was_indexed is False when the canonical URL already exists with an
    identical content_hash (no-op, avoids duplicate indexing work).
    """
    existing = db.execute(
        select(Document).where(Document.canonical_url == canonical_url)
    ).scalar_one_or_none()

    if existing and existing.content_hash == parsed.content_hash:
        return existing, False

    tokens = tokenize(parsed.text)

    if existing:
        existing.url = url
        existing.title = parsed.title
        existing.content = parsed.text
        existing.content_hash = parsed.content_hash
        existing.word_count = word_count(parsed.text)
        existing.status = DocumentStatus.INDEXED
        document = existing
    else:
        document = Document(
            url=url,
            canonical_url=canonical_url,
            title=parsed.title,
            content=parsed.text,
            content_hash=parsed.content_hash,
            word_count=word_count(parsed.text),
            status=DocumentStatus.INDEXED,
        )
        db.add(document)

    db.commit()
    db.refresh(document)

    index = get_index()
    index.add_document(document.id, tokens)
    persist_index()

    return document, True


def rebuild_index_from_documents(db: Session) -> int:
    """Full rebuild: clear the in-memory index and re-tokenize every stored document."""
    from app.search.index_store import reset_index

    reset_index()
    index = get_index()

    documents = db.execute(select(Document).where(Document.status == DocumentStatus.INDEXED)).scalars().all()
    for doc in documents:
        tokens = tokenize(doc.content)
        index.add_document(doc.id, tokens)

    persist_index()
    return len(documents)
