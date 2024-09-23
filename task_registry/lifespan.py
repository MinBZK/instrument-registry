import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from task_registry.core.config import PROJECT_NAME, VERSION, get_settings
from task_registry.core.log import configure_logging
from task_registry.data import create_urn_mappper, generate_index

CACHED_DATA: dict[str, Any] = {}

configure_logging(get_settings().LOGGING_LEVEL, get_settings().LOGGING_CONFIG)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info(f"Starting {PROJECT_NAME} version {VERSION}")
    CACHED_DATA["index"] = generate_index()
    CACHED_DATA["urn_mapper"] = create_urn_mappper(CACHED_DATA["index"]["entries"])
    yield
    CACHED_DATA.clear()
    logger.info(f"Stopping application {PROJECT_NAME} version {VERSION}")
    logging.shutdown()
