import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db import models  # noqa: F401
from app.db.session import get_db
from app.main import app
from app.search.inverted_index import InvertedIndex
from app.search import index_store


@pytest.fixture()
def client(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Isolate the search index per test so nothing leaks between tests / real disk.
    test_index = InvertedIndex()
    monkeypatch.setattr(index_store, "_index", test_index)
    monkeypatch.setattr(index_store, "persist_index", lambda: None)

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_search_rejects_empty_query(client):
    resp = client.get("/api/v1/search", params={"q": " "})
    assert resp.status_code == 400


def test_search_rejects_query_too_long(client):
    resp = client.get("/api/v1/search", params={"q": "a" * 501})
    assert resp.status_code == 400


def test_search_no_results_returns_empty_list(client):
    resp = client.get("/api/v1/search", params={"q": "nonexistentqueryterm"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["results"] == []
    assert body["total"] == 0


def test_search_pagination_limit_bounds(client):
    resp = client.get("/api/v1/search", params={"q": "test", "limit": 51})
    assert resp.status_code == 422  # FastAPI query validation catches this first

    resp2 = client.get("/api/v1/search", params={"q": "test", "page": 0})
    assert resp2.status_code == 422


def test_document_not_found_returns_404(client):
    resp = client.get("/api/v1/documents/does-not-exist")
    assert resp.status_code == 404


def test_crawl_requires_admin_auth(client):
    resp = client.post("/api/v1/crawl", json={"seed_url": "https://example.com", "max_pages": 5, "max_depth": 1})
    assert resp.status_code == 401


def test_crawl_rejects_ssrf_url_even_for_admin(client, monkeypatch):
    from app.api import deps

    def fake_admin():
        return deps.CurrentUser(username="admin", role="admin")

    app.dependency_overrides[deps.require_admin] = fake_admin
    resp = client.post("/api/v1/crawl", json={"seed_url": "http://127.0.0.1/", "max_pages": 5, "max_depth": 1})
    assert resp.status_code == 400
    app.dependency_overrides.pop(deps.require_admin, None)


def test_admin_endpoints_require_admin_role(client):
    resp = client.post("/api/v1/admin/index/rebuild")
    assert resp.status_code == 401

    resp2 = client.post("/api/v1/admin/cache/clear")
    assert resp2.status_code == 401


def test_stats_endpoint_is_public(client):
    resp = client.get("/api/v1/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert "document_count" in body
    assert "indexed_terms" in body


def test_login_rejects_invalid_credentials(client):
    resp = client.post("/api/v1/auth/login", json={"username": "nobody", "password": "wrong"})
    assert resp.status_code == 401


def test_404_and_500_never_leak_internals(client):
    resp = client.get("/api/v1/documents/nonexistent-id")
    assert resp.status_code == 404
    assert "Traceback" not in resp.text
