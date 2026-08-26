import pytest

from app.services.search_service import InvalidQueryError, validate_pagination, validate_query


def test_validate_query_rejects_empty():
    with pytest.raises(InvalidQueryError):
        validate_query("")
    with pytest.raises(InvalidQueryError):
        validate_query("   ")


def test_validate_query_rejects_too_long():
    with pytest.raises(InvalidQueryError):
        validate_query("a" * 501)


def test_validate_query_accepts_valid():
    assert validate_query("  hello world  ") == "hello world"


def test_validate_pagination_rejects_bad_page():
    with pytest.raises(InvalidQueryError):
        validate_pagination(0, 10)


def test_validate_pagination_rejects_bad_limit():
    with pytest.raises(InvalidQueryError):
        validate_pagination(1, 0)
    with pytest.raises(InvalidQueryError):
        validate_pagination(1, 51)


def test_validate_pagination_accepts_valid():
    assert validate_pagination(2, 25) == (2, 25)
