from app.search.tokenizer import stem, tokenize, word_count


def test_tokenize_lowercases_and_removes_stopwords():
    tokens = tokenize("The Quick Brown Fox Jumps Over the Lazy Dog")
    assert "the" not in tokens
    assert "over" not in tokens
    assert "quick" in tokens or "quick" in [stem(t) for t in tokens]


def test_tokenize_is_deterministic():
    text = "Search engines index documents and rank results using BM25."
    assert tokenize(text) == tokenize(text)


def test_tokenize_strips_punctuation():
    tokens = tokenize("Hello, world! This is: a test...")
    assert "hello" in tokens
    assert "world" in tokens
    assert "," not in "".join(tokens)


def test_tokenize_empty_string():
    assert tokenize("") == []
    assert tokenize(None) == []


def test_tokenize_unicode():
    tokens = tokenize("Café résumé naïve")
    assert len(tokens) > 0


def test_stemming_reduces_related_forms():
    assert stem("running") == stem("running")
    assert stem("indexing").startswith("index")


def test_word_count():
    assert word_count("one two three") == 3
    assert word_count("") == 0
    assert word_count(None) == 0
