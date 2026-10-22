from instrument_registry import urn


def test_exact_urn_matches() -> None:
    assert urn.matches("urn:nl:dpia", "urn:nl:dpia")


def test_versionless_query_matches_a_versioned_urn() -> None:
    assert urn.matches("urn:nl:aivt:ir:dpia", "urn:nl:aivt:ir:dpia:3.0")


def test_other_urn_does_not_match() -> None:
    assert not urn.matches("urn:nl:iama", "urn:nl:dpia")


def test_prefix_of_a_segment_does_not_match() -> None:
    assert not urn.matches("urn:nl:dp", "urn:nl:dpia")


def test_surrounding_whitespace_is_ignored() -> None:
    assert urn.matches("  urn:nl:dpia  ", "urn:nl:dpia")


def test_resolve_picks_the_matching_document() -> None:
    documents = {"dpia.yaml": "urn:nl:dpia", "iama.yaml": "urn:nl:iama"}

    assert urn.resolve("urn:nl:iama", documents) == "iama.yaml"


def test_resolve_returns_none_when_absent() -> None:
    assert urn.resolve("urn:nl:onbekend", {"dpia.yaml": "urn:nl:dpia"}) is None
