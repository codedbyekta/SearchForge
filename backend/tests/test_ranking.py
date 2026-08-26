from app.search import bm25, tfidf
from app.search.inverted_index import InvertedIndex


def _build_sample_index() -> InvertedIndex:
    index = InvertedIndex()
    index.add_document("doc1", ["search", "engine", "search", "index"])
    index.add_document("doc2", ["search", "ranking", "algorithm"])
    index.add_document("doc3", ["cooking", "recipe", "food"])
    return index


def test_tfidf_ranks_relevant_doc_higher():
    index = _build_sample_index()
    ranked = tfidf.rank(index, ["search"])
    ranked_ids = [doc_id for doc_id, _ in ranked]
    assert "doc3" not in ranked_ids
    assert ranked_ids[0] in ("doc1", "doc2")


def test_tfidf_no_matches_returns_empty():
    index = _build_sample_index()
    assert tfidf.rank(index, ["nonexistentterm"]) == []


def test_bm25_ranks_higher_term_frequency_higher():
    index = _build_sample_index()
    ranked = bm25.rank(index, ["search"])
    ranked_ids = [doc_id for doc_id, _ in ranked]
    # doc1 has "search" twice, doc2 has it once -> doc1 should rank first
    assert ranked_ids[0] == "doc1"


def test_bm25_respects_k1_b_parameters():
    index = _build_sample_index()
    default_score = bm25.score_document(index, "doc1", ["search"])
    high_k1_score = bm25.score_document(index, "doc1", ["search"], k1=5.0, b=0.75)
    assert default_score != high_k1_score


def test_bm25_multi_term_query():
    index = _build_sample_index()
    ranked = bm25.rank(index, ["search", "ranking"])
    ranked_ids = [doc_id for doc_id, _ in ranked]
    assert set(ranked_ids) == {"doc1", "doc2"}


def test_bm25_empty_query_terms():
    index = _build_sample_index()
    assert bm25.rank(index, []) == []
