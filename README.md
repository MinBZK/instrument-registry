# Instrument Registry

## Description

Registry of assessment schemas and assessment content (DPIA, IAMA, pre-scan)
used to determine which privacy and algorithm-impact instruments apply.

The registry serves this content over HTTP, following the interface of
[MinBZK/task-registry](https://github.com/MinBZK/task-registry): an index per
collection plus lookup by URN. Consumers that already speak that protocol can
reuse the same client code.

## Waar de bron leeft

Deze repo is de bron van de instrumenten (`mode = "authoritative"` in
`registry.toml`). Wijzigingen komen via pull requests op deze repo. De eerste
inhoud is overgenomen uit
[MinBZK/par-dpia-form](https://github.com/MinBZK/par-dpia-form); nieuwe wijzigingen horen
hier, niet daar.

## Status en verantwoordelijke

Elk instrument legt in zijn yaml vast welke organisatie ervoor verantwoordelijk
is en wat de status is (`concept` of `vastgesteld`). Het schema
`assessment-definition.v3` maakt beide velden verplicht, en de index van
`/assessments` toont ze per instrument. `assessment-definition.v2` blijft
ongewijzigd beschikbaar voor afnemers die erop pinnen.

```yaml
status: vastgesteld
verantwoordelijke:
  organisatie: Ministerie van Binnenlandse Zaken
  naam: CIO Rijk
  email: privacy-ciorijk@minbzk.nl
```

## Endpoints

| Endpoint | Levert |
| --- | --- |
| `GET /assessments` | index van de instrumenten |
| `GET /assessments/urn/{urn}` | één instrument |
| `GET /begrippenkaders` | index van de begrippenkaders |
| `GET /begrippenkaders/urn/{urn}` | één begrippenkader |
| `GET /schemas` | index van de JSON-Schema's |
| `GET /schemas/{naam}` | één JSON-Schema |
| `GET /health` | status van de dienst |

Documenten komen standaard als JSON. Met `?format=yaml` of
`Accept: application/yaml` komt de yaml zoals die in git staat, byte-identiek.

Elke response draagt een `ETag` over de inhoud. De inhoud wijzigt alleen bij een
nieuwe publicatie, dus afnemers kunnen cachen en met `If-None-Match` goedkoop
controleren op wijzigingen.

## Repository

* `assessments/` — de instrumenten en begrippenkaders.
* `schemas/` — JSON-Schema's voor assessment-definition, assessment-output en
  begrippenkader.
* `instrument_registry/` — de dienst: validatie, URN-resolutie, API.
* `urns.lock.json` — de URN's die de registry heeft gepubliceerd. Verdwijnt of
  verhuist er een, dan faalt de validatie: afnemers pinnen erop.

## Development

This project uses the Poetry package manager and Python 3.11.

* `script/serve` — draai de registry lokaal
* `script/check-mode` — controleer of een wijziging langs het toegestane pad gaat
* `script/format` — format code
* `script/lint` — lint code
* `script/test` — run tests
