FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN pip install --no-cache-dir poetry==1.8.3

COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-root --no-interaction

COPY instrument_registry ./instrument_registry
COPY assessments ./assessments
COPY schemas ./schemas
COPY registry.toml urns.lock.json ./

ARG REGISTRY_VERSION=development
ENV REGISTRY_VERSION=${REGISTRY_VERSION}

RUN python -m instrument_registry

RUN useradd --uid 10001 --no-create-home registry
USER registry

EXPOSE 8000
CMD ["uvicorn", "instrument_registry.api:app", "--host", "0.0.0.0", "--port", "8000"]
