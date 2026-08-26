"""Process-wide singleton for the in-memory inverted index."""
from app.core.config import get_settings
from app.search.inverted_index import InvertedIndex

settings = get_settings()

_INDEX_FILE = f"{settings.INDEX_STORAGE_PATH}/inverted_index.json"
_index: InvertedIndex | None = None


def get_index() -> InvertedIndex:
    global _index
    if _index is None:
        _index = InvertedIndex.load(_INDEX_FILE)
    return _index


def persist_index() -> None:
    get_index().save(_INDEX_FILE)


def reset_index() -> None:
    global _index
    _index = InvertedIndex()
    persist_index()
