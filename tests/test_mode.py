import pytest

from instrument_registry import mode


def test_mirror_rejects_manual_content_edits() -> None:
    violations = mode.check_manual_edits("mirror", ["assessments/dpia.yaml", "README.md"])

    assert violations == ["assessments/dpia.yaml"]


def test_mirror_rejects_manual_schema_edits() -> None:
    violations = mode.check_manual_edits("mirror", ["schemas/begrippenkader.v1.schema.json"])

    assert violations == ["schemas/begrippenkader.v1.schema.json"]


def test_mirror_allows_edits_outside_content() -> None:
    assert mode.check_manual_edits("mirror", ["instrument_registry/api.py", "tests/test_mode.py"]) == []


def test_authoritative_allows_content_edits() -> None:
    assert mode.check_manual_edits("authoritative", ["assessments/dpia.yaml"]) == []


def test_unknown_mode_is_rejected() -> None:
    with pytest.raises(ValueError, match="onbekende mode"):
        mode.check_manual_edits("halfslachtig", [])


def test_registry_toml_declares_a_known_mode() -> None:
    assert mode.load_mode() in {"mirror", "authoritative"}
