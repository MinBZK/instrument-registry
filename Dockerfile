ARG PYTHON_VERSION=3.12-slim

FROM  --platform=$BUILDPLATFORM python:${PYTHON_VERSION} AS project-base

LABEL maintainer=ai-validatie@minbzk.nl \
    organization=MinBZK \
    license=EUPL-1.2 \
    org.opencontainers.image.description="Instrument Registry" \
    org.opencontainers.image.source=https://github.com/MinBZK/instrument-registry \
    org.opencontainers.image.licenses=EUPL-1.2

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    POETRY_HOME='/usr/local'

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN  curl --proto "=https" -sSL https://install.python-poetry.org | python3 -

WORKDIR /app/
COPY ./poetry.lock ./pyproject.toml ./
COPY ./instruments/ ./instruments/
COPY ./script/ ./script/

RUN poetry install
ENV PATH="/app/.venv/bin:$PATH"
RUN python script/deploy

FROM project-base AS development

COPY instrument-registry/ ./instrument-registry/
COPY ./tests/ ./tests/
COPY ./README.md ./README.md
RUN poetry install


FROM development AS lint
COPY ./.prettierrc ./.prettierignore ./
RUN ruff format --check
RUN npm run prettier:check
RUN ruff check
RUN npm run lint
RUN pyright

FROM project-base AS production


RUN groupadd ir && \
    adduser --uid 100 --system --ingroup ir ir

RUN chown ir:ir /app/

USER ir

COPY --chown=root:root --chmod=755 instrument_registry /app/instrument_registry
COPY --chown=root:root --chmod=755 instruments /app/instruments
COPY --chown=root:root --chmod=755 LICENSE /app/LICENSE
COPY --chown=ir:ir --chmod=755 docker-entrypoint.sh /app/docker-entrypoint.sh

ENV PYTHONPATH=/app/
WORKDIR /app/

ENV PATH="/app/:$PATH"

CMD [ "docker-entrypoint.sh" ]
