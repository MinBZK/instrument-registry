from dataclasses import dataclass
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = ROOT / "schemas"
ASSESSMENTS_DIR = ROOT / "assessments"

# Maps assessment file name to the schema file that validates it.
#
# The begrippenkader_*.yaml files are intentionally excluded: neither
# conforms to begrippenkader.v1.schema.json as it exists upstream in
# par-dpia-form (begrippenkader_dpia.yaml uses "definitions"/"version_date"
# where the schema expects "glossary"/"metadata"; begrippenkader_iama.yaml
# predates the schema entirely). They are kept here as reference content.
ASSESSMENT_SCHEMAS = {
    "dpia.yaml": "assessment-definition.v2.schema.json",
    "iama.yaml": "assessment-definition.v2.schema.json",
    "prescan.yaml": "assessment-definition.v2.schema.json",
}


@dataclass
class ValidationError:
    file: str
    message: str


def validate_all() -> list[ValidationError]:
    errors: list[ValidationError] = []
    for assessment_file, schema_file in ASSESSMENT_SCHEMAS.items():
        schema = yaml.safe_load((SCHEMAS_DIR / schema_file).read_text())
        instance = yaml.safe_load((ASSESSMENTS_DIR / assessment_file).read_text())
        validator = Draft202012Validator(schema)
        for error in validator.iter_errors(instance):  # pyright: ignore[reportUnknownMemberType]
            errors.append(ValidationError(file=assessment_file, message=error.message))
    return errors
