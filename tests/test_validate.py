import pytest

from instrument_registry import validate


def test_assessments_conform_to_schemas() -> None:
    errors = validate.validate_all()
    assert errors == []


def test_validate_all_reports_schema_violations(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(validate.ASSESSMENT_SCHEMAS, "prescan.yaml", "begrippenkader.v1.schema.json")

    errors = validate.validate_all()

    assert any(error.file == "prescan.yaml" for error in errors)
