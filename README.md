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

## Status en eigenaar

Elk instrument legt in zijn yaml vast welke organisatie er eigenaar van is en
wat de status is (`concept` of `vastgesteld`). Het schema
`assessment-definition.v3` maakt beide velden verplicht, en de index van
`/assessments` toont ze per instrument. `assessment-definition.v2` blijft
ongewijzigd beschikbaar voor afnemers die erop pinnen.

```yaml
status: vastgesteld
eigenaar:
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

## Releases

Versies volgen de GitHub-releases. Een release maken gaat zo:

1. Zet in `pyproject.toml` de nieuwe versie (`0.2.0`) via een pull request.
2. Publiceer op GitHub een release met tag `v0.2.0`.

De workflow `release` bouwt dan de image `ghcr.io/minbzk/instrument-registry:v0.2.0`
(en `latest`). Afnemers zien de versie terug als `registry_version` in elke
index. Past de tag niet bij `pyproject.toml`, dan bouwt de workflow niets.
Elke push naar `main` levert de image `main`, met `registry_version`
`main-<korte sha>`.

## Repository

* `assessments/` — de instrumenten en begrippenkaders.
* `schemas/` — JSON-Schema's voor assessment-definition, assessment-output en
  begrippenkader.
* `instrument_registry/` — de dienst: validatie, URN-resolutie, API.
* `urns.lock.json` — de URN's die de registry heeft gepubliceerd. Verdwijnt of
  verhuist er een, dan faalt de validatie: afnemers pinnen erop.

## Relaties tussen instrumenten

Een vraag kan via `references` verwijzen naar een vraag in een ander
instrument, om een antwoord te tonen (pre-view) of over te nemen (pre-fill,
one-to-one, ...). De validatie (`python -m instrument_registry`) faalt als:

* een verwijzing naar een onbekend instrument of een onbekende vraag wijst;
* verwijzingen een cirkel vormen;
* een keten langer is dan `MAX_CHAIN_LENGTH` verwijzingen (nu 3).

## Development

This project uses the Poetry package manager and Python 3.11.

* `script/serve` — draai de registry lokaal
* `script/check-mode` — controleer of een wijziging langs het toegestane pad gaat
* `script/format` — format code
* `script/lint` — lint code
* `script/test` — run tests
