import tempfile

from app.search.inverted_index import InvertedIndex


def test_add_and_search_document():
    index = InvertedIndex()
    index.add_document("doc1", ["search", "engine", "index"])
    index.add_document("doc2", ["search", "ranking"])

    results = index.search(["search"])
    assert set(results) == {"doc1", "doc2"}


def test_get_postings_term_frequency():
    index = InvertedIndex()
    index.add_document("doc1", ["cat", "dog", "cat", "cat"])
    postings = index.get_postings("cat")
    assert postings["doc1"].term_frequency == 3


def test_missing_term_returns_empty():
    index = InvertedIndex()
    index.add_document("doc1", ["alpha"])
    assert index.search(["zeta"]) == []
    assert index.get_postings("zeta") == {}


def test_remove_document():
    index = InvertedIndex()
    index.add_document("doc1", ["alpha", "beta"])
    index.add_document("doc2", ["alpha"])

    removed = index.remove_document("doc1")
    assert removed is True
    assert "doc1" not in index.search(["alpha"])
    assert "doc2" in index.search(["alpha"])
    assert index.remove_document("doc1") is False  # already gone


def test_duplicate_add_is_idempotent_replacement():
    index = InvertedIndex()
    index.add_document("doc1", ["alpha", "alpha"])
    index.add_document("doc1", ["beta"])  # re-index same doc_id

    assert index.get_postings("alpha") == {}
    assert "doc1" in index.search(["beta"])
    assert index.total_docs == 1


def test_document_frequency_and_idf():
    index = InvertedIndex()
    index.add_document("doc1", ["common", "rare"])
    index.add_document("doc2", ["common"])
    index.add_document("doc3", ["common"])

    assert index.document_frequency("common") == 3
    assert index.document_frequency("rare") == 1
    assert index.idf("rare") > index.idf("common")


def test_average_doc_length():
    index = InvertedIndex()
    index.add_document("doc1", ["a", "b"])
    index.add_document("doc2", ["a", "b", "c", "d"])
    assert index.average_doc_length() == 3.0


def test_persistence_round_trip():
    index = InvertedIndex()
    index.add_document("doc1", ["search", "forge"])
    index.add_document("doc2", ["forge", "engine"])

    with tempfile.TemporaryDirectory() as tmp:
        path = f"{tmp}/index.json"
        index.save(path)
        loaded = InvertedIndex.load(path)

        assert loaded.total_docs == index.total_docs
        assert set(loaded.search(["forge"])) == {"doc1", "doc2"}
        assert loaded.get_postings("search")["doc1"].term_frequency == 1


def test_load_missing_file_returns_empty_index():
    loaded = InvertedIndex.load("/tmp/does_not_exist_searchforge.json")
    assert loaded.total_docs == 0
    assert loaded.search(["anything"]) == []
