"""TF-IDF ranking (Development Plan Phase 4 / PRD F6)."""
import math
from typing import Dict, List, Tuple

from app.search.inverted_index import InvertedIndex


def score_document(index: InvertedIndex, doc_id: str, query_terms: List[str]) -> float:
    """Sum of tf-idf weights (log-scaled tf * smoothed idf) over query terms."""
    score = 0.0
    for term in query_terms:
        postings = index.get_postings(term)
        posting = postings.get(doc_id)
        if not posting:
            continue
        tf_weight = 1.0 + math.log(posting.term_frequency)
        score += tf_weight * index.idf(term, smoothing=False)
    return score


def rank(index: InvertedIndex, query_terms: List[str]) -> List[Tuple[str, float]]:
    """Return (doc_id, score) pairs sorted by score descending."""
    candidate_ids = index.search(query_terms)
    scored: Dict[str, float] = {
        doc_id: score_document(index, doc_id, query_terms) for doc_id in candidate_ids
    }
    return sorted(scored.items(), key=lambda kv: kv[1], reverse=True)
