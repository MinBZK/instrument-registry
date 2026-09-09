# Instrument Registry

## Description

Registry of assessment schemas and assessment content (DPIA, IAMA, pre-scan)
used to determine which privacy and algorithm-impact instruments apply.

The registry serves this content over HTTP, following the interface of
[MinBZK/task-registry](https://github.com/MinBZK/task-registry): an index per
collection plus lookup by URN. Consumers that already speak that protocol can
reuse the same client code.

## Waar de bron leeft

`registry.toml` bepaalt wie de inhoud mag schrijven.

* `mode = "mirror"` (huidige stand) — de bron leeft in
  [MinBZK/par-dpia-form](https://github.com/MinBZK/par-dpia-form). Deze repo
  publiceert een kopie die uitsluitend door de sync-workflow wordt bijgewerkt.
  `assessments/PROVENANCE.json` legt vast uit welke upstream-commit de huidige
  inhoud komt.
* `mode = "authoritative"` — de bron leeft hier; wijzigingen komen via pull
  requests op deze repo.

De overgang tussen die twee is één pull request: `mode` omzetten, het
`[content.upstream]`-blok verwijderen en de sync-workflow weghalen. De indeling
van de repo, de URL's en de URN's blijven gelijk, dus afnemers merken er niets
van.

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
* `instrument_registry/` — de dienst: validatie, sync, URN-resolutie, API.
* `urns.lock.json` — de URN's die de registry heeft gepubliceerd. Verdwijnt of
  verhuist er een, dan faalt de validatie: afnemers pinnen erop.

## Development

This project uses the Poetry package manager and Python 3.11.

* `script/serve` — draai de registry lokaal
* `script/sync` — haal de inhoud op bij de bron (alleen in mirror-stand)
* `script/check-mode` — controleer of een wijziging langs het toegestane pad gaat
* `script/format` — format code
* `script/lint` — lint code
* `script/test` — run tests
