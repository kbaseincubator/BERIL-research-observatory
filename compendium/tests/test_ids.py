"""Foundation tests: deterministic normalization + content hashing are stable & order-free."""

from compendium import ids


def test_normalize_is_nfkc_lowercased_and_collapses_whitespace():
    a = ids.normalize("Acinetobacter baylyi ADP1")
    b = ids.normalize("  acinetobacter   baylyi  adp1 ")  # whitespace/case differ
    assert a == b == "acinetobacter baylyi adp1"
    # punctuation is stripped to spaces, then collapsed
    assert ids.normalize("genes are core-enriched!") == "genes are core enriched"
    assert ids.normalize(None) == ""


def test_content_hash_is_deterministic_and_order_sensitive():
    h1 = ids.content_hash("a", "b", "c")
    assert h1 == ids.content_hash("a", "b", "c")
    # concatenation order matters
    assert ids.content_hash("a", "b") != ids.content_hash("b", "a")
    # None parts are treated as empty strings
    assert ids.content_hash("a", None, "b") == ids.content_hash("a", "", "b")
    # digest length is configurable
    assert len(ids.content_hash("x", n=16)) == 16
    assert len(ids.content_hash("x", n=8)) == 8
