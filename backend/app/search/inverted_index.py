"""
Custom inverted index (Development Plan Phase 3 / PRD F4).

This is a from-scratch, application-owned data structure — deliberately NOT
delegated to PostgreSQL full-text search (System Architecture 3.8: "the
custom application-managed inverted index is kept separately").

Structure:
    postings[term] = { doc_id: Posting(term_frequency, positions=[...]) }
    doc_lengths[doc_id] = number of tokens in the document
    doc_frequency(term) = number of documents containing `term`  (len(postings[term]))

Persisted to a single JSON file (System Architecture 3.8 allows "serialized
files or another project-owned persistent structure" for the MVP).
"""
from __future__ import annotations

import json
import math
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass
class Posting:
    term_frequency: int = 0
    positions: List[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"tf": self.term_frequency, "positions": self.positions}

    @staticmethod
    def from_dict(d: dict) -> "Posting":
        return Posting(term_frequency=d["tf"], positions=d.get("positions", []))


class InvertedIndex:
    """Thread-safe in-memory inverted index with JSON persistence."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # term -> {doc_id -> Posting}
        self._postings: Dict[str, Dict[str, Posting]] = {}
        # doc_id -> token count (for BM25 length normalization)
        self._doc_lengths: Dict[str, int] = {}
        # doc_id -> original title, kept only for debugging/inspection
        self.total_docs: int = 0

    # ---------------------------------------------------------------- CRUD

    def add_document(self, doc_id: str, tokens: List[str]) -> None:
        """
        Index (or re-index) a document's tokens.

        If the document already exists, it is removed first, so re-indexing
        the same doc_id is idempotent (SRS: "cannot be indexed twice under
        the same canonical URL/version" is enforced at the service layer;
        the index itself supports safe replacement).
        """
        with self._lock:
            if doc_id in self._doc_lengths:
                self.remove_document(doc_id)

            for position, term in enumerate(tokens):
                bucket = self._postings.setdefault(term, {})
                posting = bucket.setdefault(doc_id, Posting())
                posting.term_frequency += 1
                posting.positions.append(position)

            self._doc_lengths[doc_id] = len(tokens)
            self.total_docs += 1

    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from the index. Returns True if it existed."""
        with self._lock:
            if doc_id not in self._doc_lengths:
                return False

            empty_terms = []
            for term, bucket in self._postings.items():
                if doc_id in bucket:
                    del bucket[doc_id]
                    if not bucket:
                        empty_terms.append(term)
            for term in empty_terms:
                del self._postings[term]

            del self._doc_lengths[doc_id]
            self.total_docs = max(0, self.total_docs - 1)
            return True

    def get_postings(self, term: str) -> Dict[str, Posting]:
        with self._lock:
            return dict(self._postings.get(term, {}))

    def document_frequency(self, term: str) -> int:
        with self._lock:
            return len(self._postings.get(term, {}))

    def doc_length(self, doc_id: str) -> int:
        with self._lock:
            return self._doc_lengths.get(doc_id, 0)

    def average_doc_length(self) -> float:
        with self._lock:
            if not self._doc_lengths:
                return 0.0
            return sum(self._doc_lengths.values()) / len(self._doc_lengths)

    def search(self, terms: Iterable[str]) -> List[str]:
        """
        Boolean OR candidate retrieval: any document containing at least one
        query term. Ranking is applied afterwards by tfidf.py / bm25.py.
        """
        with self._lock:
            candidates = set()
            for term in terms:
                candidates.update(self._postings.get(term, {}).keys())
            return list(candidates)

    def idf(self, term: str, smoothing: bool = True) -> float:
        """Inverse document frequency, classic smoothed formulation."""
        with self._lock:
            n = self.total_docs
            df = self.document_frequency(term)
            if n == 0:
                return 0.0
            if smoothing:
                return math.log((n - df + 0.5) / (df + 0.5) + 1.0)
            if df == 0:
                return 0.0
            return math.log(n / df)

    # ------------------------------------------------------------ persist

    def save(self, path: str) -> None:
        with self._lock:
            payload = {
                "total_docs": self.total_docs,
                "doc_lengths": self._doc_lengths,
                "postings": {
                    term: {doc_id: p.to_dict() for doc_id, p in bucket.items()}
                    for term, bucket in self._postings.items()
                },
            }
        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = out_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        tmp_path.replace(out_path)  # atomic-ish swap

    @classmethod
    def load(cls, path: str) -> "InvertedIndex":
        idx = cls()
        p = Path(path)
        if not p.exists():
            return idx
        with open(p, "r", encoding="utf-8") as f:
            payload = json.load(f)
        idx.total_docs = payload.get("total_docs", 0)
        idx._doc_lengths = payload.get("doc_lengths", {})
        idx._postings = {
            term: {doc_id: Posting.from_dict(d) for doc_id, d in bucket.items()}
            for term, bucket in payload.get("postings", {}).items()
        }
        return idx

    def term_count(self) -> int:
        with self._lock:
            return len(self._postings)

    def clear(self) -> None:
        with self._lock:
            self._postings.clear()
            self._doc_lengths.clear()
            self.total_docs = 0
