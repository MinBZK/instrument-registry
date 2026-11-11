from instrument_registry import urn


def test_exact_urn_matches() -> None:
    assert urn.matches("urn:nl:minbzk:ir:dpia:3.0", "urn:nl:minbzk:ir:dpia:3.0")


def test_versionless_query_matches_a_versioned_urn() -> None:
    assert urn.matches("urn:nl:minbzk:ir:dpia", "urn:nl:minbzk:ir:dpia:3.0")


def test_other_version_does_not_match() -> None:
    assert not urn.matches("urn:nl:minbzk:ir:dpia:2.0", "urn:nl:minbzk:ir:dpia:3.0")


def test_other_urn_does_not_match() -> None:
    assert not urn.matches("urn:nl:minbzk:ir:iama", "urn:nl:minbzk:ir:dpia:3.0")


def test_other_organisation_does_not_match() -> None:
    assert not urn.matches("urn:nl:minfin:ir:dpia", "urn:nl:minbzk:ir:dpia:3.0")


def test_prefix_of_a_segment_does_not_match() -> None:
    assert not urn.matches("urn:nl:minbzk:ir:dp", "urn:nl:minbzk:ir:dpia:3.0")


def test_organisation_alone_does_not_match() -> None:
    assert not urn.matches("urn:nl:minbzk", "urn:nl:minbzk:ir:dpia:3.0")
    assert not urn.matches("urn:nl:minbzk:ir", "urn:nl:minbzk:ir:dpia:3.0")


def test_surrounding_whitespace_is_ignored() -> None:
    assert urn.matches("  urn:nl:minbzk:ir:dpia:3.0  ", "urn:nl:minbzk:ir:dpia:3.0")


def test_parse_splits_the_parts() -> None:
    assert urn.parse("urn:nl:minfin:ir:begrippenkader-dpia:1.0.0") == urn.Urn(
        organisation="minfin", name="begrippenkader-dpia", version="1.0.0"
    )


def test_parse_rejects_malformed_urns() -> None:
    assert urn.parse("urn:nl:dpia") is None
    assert urn.parse("urn:nl:minbzk:ir:dpia") is None
    assert urn.parse("urn:nl:minbzk:tr:dpia:3.0") is None
    assert urn.parse("urn:nl:MinBZK:ir:dpia:3.0") is None
    assert urn.parse("urn:nl:org1:ir:dpia:3.0") is None


def test_organisation_need_not_be_a_ministry() -> None:
    assert urn.parse("urn:nl:duo:ir:dpia:1.0") == urn.Urn(organisation="duo", name="dpia", version="1.0")
    assert urn.parse("urn:nl:bd:ir:dpia:1.0") is not None


def test_base_drops_the_version() -> None:
    assert urn.base("urn:nl:minbzk:ir:dpia:3.0") == "urn:nl:minbzk:ir:dpia"


def test_urn_renders_back_to_its_string() -> None:
    assert str(urn.Urn(organisation="minbzk", name="dpia", version="3.0")) == "urn:nl:minbzk:ir:dpia:3.0"


def test_resolve_picks_the_matching_document() -> None:
    documents = {"dpia.yaml": "urn:nl:minbzk:ir:dpia:3.0", "iama.yaml": "urn:nl:minbzk:ir:iama:2.0"}

    assert urn.resolve("urn:nl:minbzk:ir:iama", documents) == "iama.yaml"


def test_resolve_returns_none_when_absent() -> None:
    assert urn.resolve("urn:nl:minbzk:ir:onbekend", {"dpia.yaml": "urn:nl:minbzk:ir:dpia:3.0"}) is None
