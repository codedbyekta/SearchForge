import pytest

from app.core.url_safety import URLSafetyError, validate_and_normalize_url
from app.crawler.url_manager import URLFrontier, canonicalize_url


def test_valid_https_url_passes():
    result = validate_and_normalize_url("https://Example.com/Path/", resolve_dns=False)
    assert result == "https://example.com/Path/"


def test_rejects_javascript_scheme():
    with pytest.raises(URLSafetyError):
        validate_and_normalize_url("javascript:alert(1)", resolve_dns=False)


def test_rejects_file_scheme():
    with pytest.raises(URLSafetyError):
        validate_and_normalize_url("file:///etc/passwd", resolve_dns=False)


def test_rejects_localhost():
    with pytest.raises(URLSafetyError):
        validate_and_normalize_url("http://localhost:8000/admin", resolve_dns=False)


def test_rejects_loopback_ip():
    with pytest.raises(URLSafetyError):
        validate_and_normalize_url("http://127.0.0.1/", resolve_dns=False)


def test_rejects_private_ip_ranges():
    for ip in ("10.0.0.5", "192.168.1.1", "172.16.0.1"):
        with pytest.raises(URLSafetyError):
            validate_and_normalize_url(f"http://{ip}/", resolve_dns=False)


def test_rejects_cloud_metadata_endpoint():
    with pytest.raises(URLSafetyError):
        validate_and_normalize_url("http://169.254.169.254/latest/meta-data/", resolve_dns=False)


def test_rejects_empty_url():
    with pytest.raises(URLSafetyError):
        validate_and_normalize_url("", resolve_dns=False)


def test_canonicalize_strips_fragment_and_tracking_params():
    canon = canonicalize_url("https://Example.com/page/?utm_source=x&id=5#section")
    assert "#" not in canon
    assert "utm_source" not in canon
    assert "id=5" in canon


def test_url_frontier_dedup():
    frontier = URLFrontier()
    assert frontier.add("https://example.com/a", 0) is True
    assert frontier.add("https://example.com/a", 0) is False  # duplicate
    assert frontier.add("https://example.com/a#frag", 0) is False  # same after canonicalization
    assert frontier.seen_count() == 1
