import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = ROOT / "schemas"
ASSESSMENTS_DIR = ROOT / "assessments"
URN_LOCK_FILE = ROOT / "urns.lock.json"

# Maps assessment file name to the schema file that validates it.
ASSESSMENT_SCHEMAS = {
    "dpia.yaml": "assessment-definition.v2.schema.json",
    "iama.yaml": "assessment-definition.v2.schema.json",
    "prescan.yaml": "assessment-definition.v2.schema.json",
    "begrippenkader_dpia.yaml": "begrippenkader.v1.schema.json",
    "begrippenkader_iama.yaml": "begrippenkader.v1.schema.json",
}


@dataclass
class ValidationError:
    file: str
    message: str


def load_documents() -> dict[str, dict[str, Any]]:
    """Read every registered assessment file, keyed by file name."""
    documents: dict[str, dict[str, Any]] = {}
    for assessment_file in ASSESSMENT_SCHEMAS:
        documents[assessment_file] = yaml.safe_load((ASSESSMENTS_DIR / assessment_file).read_text())
    return documents


def check_schemas(documents: dict[str, dict[str, Any]]) -> list[ValidationError]:
    """Validate each document against the schema registered for it."""
    errors: list[ValidationError] = []
    for file_name, document in documents.items():
        schema_file = ASSESSMENT_SCHEMAS.get(file_name)
        if schema_file is None:
            continue
        schema = yaml.safe_load((SCHEMAS_DIR / schema_file).read_text())
        validator = Draft202012Validator(schema)
        for error in validator.iter_errors(document):  # pyright: ignore[reportUnknownMemberType]
            errors.append(ValidationError(file=file_name, message=error.message))
    return errors


def check_unique_urns(documents: dict[str, dict[str, Any]]) -> list[ValidationError]:
    """Report every document whose URN was already claimed by an earlier one."""
    errors: list[ValidationError] = []
    seen: dict[str, str] = {}
    for file_name, document in documents.items():
        urn = document.get("urn")
        if not isinstance(urn, str):
            continue
        if urn in seen:
            errors.append(ValidationError(file=file_name, message=f"URN {urn} is already used by {seen[urn]}"))
            continue
        seen[urn] = file_name
    return errors


def check_term_references(documents: dict[str, dict[str, Any]]) -> list[ValidationError]:
    """Report alternative terms pointing at a definition id that does not exist."""
    errors: list[ValidationError] = []
    for file_name, document in documents.items():
        definition_ids = {
            definition["id"] for definition in document.get("definitions", []) if isinstance(definition.get("id"), str)
        }
        for alternative in document.get("alternative_terms", []):
            voorkeur_id = alternative.get("voorkeur_id")
            if isinstance(voorkeur_id, str) and voorkeur_id not in definition_ids:
                errors.append(
                    ValidationError(
                        file=file_name,
                        message=f"alternative term {alternative.get('id', '?')} refers to unknown id {voorkeur_id}",
                    )
                )
    return errors


def load_locked_urns() -> dict[str, str]:
    """Read the URNs the registry has published before, mapped to their file name."""
    if not URN_LOCK_FILE.exists():
        return {}
    locked: dict[str, str] = json.loads(URN_LOCK_FILE.read_text())
    return locked


def check_urn_stability(documents: dict[str, dict[str, Any]], locked: dict[str, str]) -> list[ValidationError]:
    """Report published URNs that disappeared or moved to another file.

    Consumers pin a URN, so losing or moving one breaks them silently. Adding
    URNs is always allowed.
    """
    errors: list[ValidationError] = []
    current = {
        document["urn"]: file_name for file_name, document in documents.items() if isinstance(document.get("urn"), str)
    }
    for urn, file_name in locked.items():
        if urn not in current:
            errors.append(ValidationError(file=file_name, message=f"published URN {urn} is no longer in the registry"))
            continue
        if current[urn] != file_name:
            errors.append(
                ValidationError(
                    file=file_name,
                    message=f"published URN {urn} moved to {current[urn]}",
                )
            )
    return errors


def validate_all() -> list[ValidationError]:
    documents = load_documents()
    return (
        check_schemas(documents)
        + check_unique_urns(documents)
        + check_term_references(documents)
        + check_urn_stability(documents, load_locked_urns())
    )
