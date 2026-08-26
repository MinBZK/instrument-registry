# Instrument Registry

## Description

Registry of assessment schemas and assessment content (DPIA, IAMA, pre-scan)
used to determine which privacy and algorithm-impact instruments apply.

The schemas and assessment definitions in this repository are copied from
[MinBZK/par-dpia-form](https://github.com/MinBZK/par-dpia-form) (see
`schemas/` and `assessments/`), which is the source of truth for these
instruments. This repository packages that content as a standalone registry,
in the spirit of [MinBZK/task-registry](https://github.com/MinBZK/task-registry).

## Structure

* `schemas/` — JSON Schemas describing the assessment-definition,
  assessment-output, and begrippenkader (terminology) formats.
* `assessments/` — Assessment content (DPIA, IAMA, pre-scan) and
  begrippenkaders, validated against the schemas above.
* `instrument_registry/` — Python package for serving/validating the registry.

## Development

This project uses the Poetry package manager and Python 3.11.

* `script/format` — format code
* `script/lint` — lint code
* `script/test` — run tests
