"""
HTML parsing (PRD F2 / Development Plan Phase 5).

Extracts title, main text, headings, and outbound links while minimizing
boilerplate (nav/footer/script/style are stripped before text extraction).
"""
import hashlib
from dataclasses import dataclass, field
from typing import List
from urllib.parse import urljoin

from selectolax.parser import HTMLParser

BOILERPLATE_TAGS = ("script", "style", "noscript", "nav", "footer", "header", "aside", "form")


@dataclass
class ParsedDocument:
    title: str
    text: str
    headings: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    content_hash: str = ""


def parse_html(html: str, base_url: str) -> ParsedDocument:
    tree = HTMLParser(html)

    # Strip boilerplate before extracting text so nav/menu/footer text
    # doesn't pollute the index.
    for tag in BOILERPLATE_TAGS:
        for node in tree.css(tag):
            node.decompose()

    title_node = tree.css_first("title")
    title = title_node.text(strip=True) if title_node else ""

    headings = [
        h.text(strip=True)
        for h in tree.css("h1, h2, h3")
        if h.text(strip=True)
    ]

    body = tree.css_first("body")
    text = body.text(separator=" ", strip=True) if body else tree.text(separator=" ", strip=True)
    # Collapse excess whitespace for a clean, deterministic content string.
    text = " ".join(text.split())

    links = []
    for a in tree.css("a[href]"):
        href = a.attributes.get("href")
        if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
            continue
        links.append(urljoin(base_url, href))

    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

    return ParsedDocument(
        title=title or base_url,
        text=text,
        headings=headings,
        links=links,
        content_hash=content_hash,
    )
