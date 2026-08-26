from app.crawler.parser import parse_html

SAMPLE_HTML = """
<html>
<head><title>Test Page Title</title></head>
<body>
  <nav>Home About Contact</nav>
  <h1>Main Heading</h1>
  <p>This is the main content of the page about search engines.</p>
  <a href="/relative-link">Relative</a>
  <a href="https://external.com/page">External</a>
  <a href="#section">Anchor</a>
  <a href="mailto:test@example.com">Email</a>
  <footer>Copyright 2026</footer>
</body>
</html>
"""


def test_parse_extracts_title():
    result = parse_html(SAMPLE_HTML, base_url="https://example.com/")
    assert result.title == "Test Page Title"


def test_parse_extracts_headings():
    result = parse_html(SAMPLE_HTML, base_url="https://example.com/")
    assert "Main Heading" in result.headings


def test_parse_strips_boilerplate():
    result = parse_html(SAMPLE_HTML, base_url="https://example.com/")
    assert "Home About Contact" not in result.text
    assert "Copyright 2026" not in result.text
    assert "main content" in result.text


def test_parse_extracts_and_resolves_links():
    result = parse_html(SAMPLE_HTML, base_url="https://example.com/")
    assert "https://example.com/relative-link" in result.links
    assert "https://external.com/page" in result.links
    assert not any(link.startswith("mailto:") for link in result.links)
    assert not any(link.startswith("#") for link in result.links)


def test_parse_produces_stable_content_hash():
    r1 = parse_html(SAMPLE_HTML, base_url="https://example.com/")
    r2 = parse_html(SAMPLE_HTML, base_url="https://example.com/")
    assert r1.content_hash == r2.content_hash


def test_parse_empty_html():
    result = parse_html("<html><body></body></html>", base_url="https://example.com/")
    assert result.text == ""
    assert result.links == []
