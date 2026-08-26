"""
Text processing pipeline (Development Plan Phase 2).

Deterministic: the same input always produces the same output tokens, which
is required so index rebuilds are reproducible.

Steps: lowercase -> unicode-normalize -> strip punctuation/symbols ->
split on whitespace -> drop stop-words -> lightweight suffix stemming.
"""
import re
import unicodedata
from typing import List

# A compact, standard English stop-word list (kept in-module so the pipeline
# has no external data dependency and stays fully deterministic).
STOPWORDS = frozenset(
    """
    a about above after again against all am an and any are aren't as at be
    because been before being below between both but by can't cannot could
    couldn't did didn't do does doesn't doing don't down during each few for
    from further had hadn't has hasn't have haven't having he he'd he'll
    he's her here here's hers herself him himself his how how's i i'd i'll
    i'm i've if in into is isn't it it's its itself let's me more most
    mustn't my myself no nor not of off on once only or other ought our
    ours ourselves out over own same shan't she she'd she'll she's should
    shouldn't so some such than that that's the their theirs them
    themselves then there there's these they they'd they'll they're
    they've this those through to too under until up very was wasn't we
    we'd we'll we're we've were weren't what what's when when's where
    where's which while who who's whom why why's with won't would
    wouldn't you you'd you'll you're you've your yours yourself yourselves
    """.split()
)

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")

# Small rule-based suffix stemmer (Porter-lite). Deterministic, dependency-free.
_STEM_RULES = [
    ("ational", "ate"),
    ("tional", "tion"),
    ("ization", "ize"),
    ("fulness", "ful"),
    ("ousness", "ous"),
    ("iveness", "ive"),
    ("ies", "y"),
    ("ing", ""),
    ("edly", ""),
    ("ed", ""),
    ("es", ""),
    ("s", ""),
]


def normalize_text(text: str) -> str:
    """Unicode-normalize and lowercase text."""
    text = unicodedata.normalize("NFKC", text)
    return text.lower()


def stem(token: str) -> str:
    """Very small, deterministic suffix-stripping stemmer."""
    if len(token) <= 3:
        return token
    for suffix, replacement in _STEM_RULES:
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            return token[: -len(suffix)] + replacement
    return token


def tokenize(
    text: str,
    remove_stopwords: bool = True,
    apply_stemming: bool = True,
) -> List[str]:
    """
    Convert raw text into a list of normalized tokens.

    This is deterministic: identical input -> identical output, every time.
    """
    if not text:
        return []

    normalized = normalize_text(text)
    raw_tokens = _TOKEN_RE.findall(normalized)

    tokens: List[str] = []
    for tok in raw_tokens:
        if remove_stopwords and tok in STOPWORDS:
            continue
        if apply_stemming:
            tok = stem(tok)
        if tok:
            tokens.append(tok)
    return tokens


def word_count(text: str) -> int:
    """Simple whitespace/word count used for Document.word_count (pre-stopword-removal)."""
    return len(re.findall(r"\S+", text or ""))
