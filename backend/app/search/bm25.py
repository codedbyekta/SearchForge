"""
BM25 ranking (Development Plan Phase 4 / PRD F6 — preferred algorithm).

score(D, Q) = sum_over_query_terms( idf(t) * (tf * (k1+1)) /
                                     (tf + k1 * (1 - b + b * |D| / avgdl)) )
"""
from typing import Dict, List, Tuple

from app.core.config import get_settings
from app.search.inverted_index import InvertedIndex

settings = get_settings()


def score_document(
    index: InvertedIndex,
    doc_id: str,
    query_terms: List[str],
    k1: float = None,
    b: float = None,
) -> float:
    k1 = settings.BM25_K1 if k1 is None else k1
    b = settings.BM25_B if b is None else b

    avgdl = index.average_doc_length() or 1.0
    doc_len = index.doc_length(doc_id) or 1

    score = 0.0
    for term in query_terms:
        postings = index.get_postings(term)
        posting = postings.get(doc_id)
        if not posting:
            continue
        tf = posting.term_frequency
        idf = index.idf(term, smoothing=True)
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * (doc_len / avgdl))
        score += idf * (numerator / denominator)
    return score


def rank(
    index: InvertedIndex,
    query_terms: List[str],
    k1: float = None,
    b: float = None,
) -> List[Tuple[str, float]]:
    """Return (doc_id, score) pairs sorted by BM25 score descending."""
    candidate_ids = index.search(query_terms)
    scored: Dict[str, float] = {
        doc_id: score_document(index, doc_id, query_terms, k1=k1, b=b) for doc_id in candidate_ids
    }
    return sorted(scored.items(), key=lambda kv: kv[1], reverse=True)
