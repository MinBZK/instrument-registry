"""Het herkennen van instrument-identifiers.

Een URN heeft de vorm `urn:nl:<organisatie>:ir:<instrument>:<versie>`, bijvoorbeeld
`urn:nl:minbzk:ir:dpia:3.0`. De organisatie is de eigenaar van het instrument:
nu nog alleen ministeries (`minbzk`, `minfin`), maar net zo goed een uitvoerder
als `duo` of `bd` (Belastingdienst). `ir` staat voor instrument registry, en de
versie is dezelfde als het `version`-veld van het document. Alle kennis over die
vorm zit in deze module, en alleen hier, zodat endpoints en afnemers er niet van
afhangen.
"""

import re
from dataclasses import dataclass

PATTERN = re.compile(
    r"^urn:nl:(?P<organisation>[a-z]+):ir:(?P<name>[a-z0-9]+(?:-[a-z0-9]+)*):(?P<version>\d+(?:\.\d+){0,2})$"
)


@dataclass(frozen=True)
class Urn:
    organisation: str
    name: str
    version: str

    @property
    def base(self) -> str:
        """The URN without version: the identity that stays stable across releases."""
        return f"urn:nl:{self.organisation}:ir:{self.name}"

    def __str__(self) -> str:
        return f"{self.base}:{self.version}"


def normalize(value: str) -> str:
    """Strip incidental whitespace from an identifier."""
    return value.strip()


def parse(value: str) -> Urn | None:
    """Split a URN into its parts, or return None when it is not well-formed."""
    match = PATTERN.match(normalize(value))
    if match is None:
        return None
    return Urn(organisation=match["organisation"], name=match["name"], version=match["version"])


def base(value: str) -> str:
    """Return the URN without its version; a malformed URN is returned as-is."""
    parsed = parse(value)
    return parsed.base if parsed else normalize(value)


def matches(query: str, candidate: str) -> bool:
    """Tell whether a query addresses a document's URN.

    An exact URN always matches. A query without version matches the versioned
    URN, so `urn:nl:minbzk:ir:dpia` resolves to the published version. Only the
    full instrument is addressed: `urn:nl:minbzk` or `urn:nl:minbzk:ir:dp` match
    nothing.
    """
    query = normalize(query)
    candidate = normalize(candidate)
    return query in (candidate, base(candidate))


def resolve(query: str, documents: dict[str, str]) -> str | None:
    """Return the key of the document a query addresses, if any."""
    for key, candidate in documents.items():
        if matches(query, candidate):
            return key
    return None
