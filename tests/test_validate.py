import pytest

from instrument_registry import validate


def test_assessments_conform_to_schemas() -> None:
    errors = validate.validate_all()
    assert errors == []


def test_validate_all_reports_schema_violations(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(validate.ASSESSMENT_SCHEMAS, "prescan.yaml", "begrippenkader.v1.schema.json")

    errors = validate.validate_all()

    assert any(error.file == "prescan.yaml" for error in errors)


def test_every_assessment_file_is_validated() -> None:
    yaml_files = {path.name for path in validate.ASSESSMENTS_DIR.glob("*.yaml")}

    assert yaml_files == set(validate.ASSESSMENT_SCHEMAS)


def test_duplicate_urns_are_reported() -> None:
    documents = {
        "dpia.yaml": {"urn": "urn:nl:dpia"},
        "kopie.yaml": {"urn": "urn:nl:dpia"},
    }

    errors = validate.check_unique_urns(documents)

    assert [error.file for error in errors] == ["kopie.yaml"]
    assert "urn:nl:dpia" in errors[0].message


def test_unique_urns_pass() -> None:
    documents = {
        "dpia.yaml": {"urn": "urn:nl:dpia"},
        "iama.yaml": {"urn": "urn:nl:iama"},
    }

    assert validate.check_unique_urns(documents) == []


def test_validate_all_reports_duplicate_urns(monkeypatch: pytest.MonkeyPatch) -> None:
    documents = {
        "dpia.yaml": {"urn": "urn:nl:dpia"},
        "iama.yaml": {"urn": "urn:nl:dpia"},
    }
    monkeypatch.setattr(validate, "load_documents", lambda: documents)

    errors = validate.validate_all()

    assert any("already used by" in error.message for error in errors)


def test_unknown_voorkeur_id_is_reported() -> None:
    documents = {
        "begrippenkader_dpia.yaml": {
            "definitions": [{"id": "verwerking", "term": "Verwerking", "definition": "x"}],
            "alternative_terms": [{"id": "bewerking", "term": "Bewerking", "voorkeur_id": "bestaat_niet"}],
        }
    }

    errors = validate.check_term_references(documents)

    assert [error.file for error in errors] == ["begrippenkader_dpia.yaml"]
    assert "bestaat_niet" in errors[0].message


def test_known_voorkeur_id_passes() -> None:
    documents = {
        "begrippenkader_dpia.yaml": {
            "definitions": [{"id": "verwerking", "term": "Verwerking", "definition": "x"}],
            "alternative_terms": [{"id": "bewerking", "term": "Bewerking", "voorkeur_id": "verwerking"}],
        }
    }

    assert validate.check_term_references(documents) == []


def test_removed_urn_is_reported() -> None:
    documents = {"dpia.yaml": {"urn": "urn:nl:dpia"}}
    locked = {"urn:nl:dpia": "dpia.yaml", "urn:nl:iama": "iama.yaml"}

    errors = validate.check_urn_stability(documents, locked)

    assert [error.file for error in errors] == ["iama.yaml"]
    assert "urn:nl:iama" in errors[0].message


def test_moved_urn_is_reported() -> None:
    documents = {"hernoemd.yaml": {"urn": "urn:nl:dpia"}}
    locked = {"urn:nl:dpia": "dpia.yaml"}

    errors = validate.check_urn_stability(documents, locked)

    assert "hernoemd.yaml" in errors[0].message


def test_added_urn_is_allowed() -> None:
    documents = {"dpia.yaml": {"urn": "urn:nl:dpia"}, "nieuw.yaml": {"urn": "urn:nl:nieuw"}}
    locked = {"urn:nl:dpia": "dpia.yaml"}

    assert validate.check_urn_stability(documents, locked) == []


def test_locked_urns_match_the_registry() -> None:
    errors = validate.check_urn_stability(validate.load_documents(), validate.load_locked_urns())

    assert errors == []
