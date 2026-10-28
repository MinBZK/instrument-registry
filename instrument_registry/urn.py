"""Het herkennen van instrument-identifiers.

De uiteindelijke vorm van de URN ligt nog niet vast: mogelijk komt de versie in
de URN zelf (`urn:nl:aivt:ir:dpia:3.0`, zoals de task registry doet), mogelijk
blijft hij in een apart veld staan. Alle kennis daarover zit in deze module, en
alleen hier, zodat die beslissing later de endpoints en de afnemers ongemoeid
laat.
"""


def normalize(value: str) -> str:
    """Strip incidental whitespace from an identifier."""
    return value.strip()


def matches(query: str, candidate: str) -> bool:
    """Tell whether a query addresses a document's URN.

    An exact URN always matches. A query without version matches a versioned
    URN, so `urn:nl:aivt:ir:dpia` resolves to the newest published version.
    Matching happens per segment: `urn:nl:dp` does not address `urn:nl:dpia`.
    """
    query = normalize(query)
    candidate = normalize(candidate)
    if query == candidate:
        return True
    return candidate.startswith(f"{query}:")


def resolve(query: str, documents: dict[str, str]) -> str | None:
    """Return the key of the document a query addresses, if any."""
    for key, candidate in documents.items():
        if matches(query, candidate):
            return key
    return None
