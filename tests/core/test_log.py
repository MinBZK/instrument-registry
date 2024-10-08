import logging

import pytest
from task_registry.core.config import Settings
from task_registry.core.log import configure_logging


def test_logging_tr_module(caplog: pytest.LogCaptureFixture):
    config = {"loggers": {"tr": {"propagate": True}}}

    configure_logging(config=config)

    logger = logging.getLogger("tr")

    message = "This is a test log message"
    logger.debug(message)  # defaults to INFO level so debug is not printed
    logger.info(message)
    logger.warning(message)
    logger.error(message)
    logger.critical(message)

    assert len(caplog.records) == 4
    assert caplog.records[0].message == message


def test_logging_submodule(caplog: pytest.LogCaptureFixture):
    config = {"loggers": {"tr": {"propagate": True}}}

    configure_logging(config=config)

    logger = logging.getLogger("tr.main")

    message = "This is a test log message"
    logger.debug(message)
    logger.info(message)  # should use module logger level
    logger.warning(message)
    logger.error(message)
    logger.critical(message)

    assert len(caplog.records) == 4
    assert caplog.records[0].message == message


def test_logging_config(caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(
        "LOGGING_CONFIG",
        '{"loggers": { "tr": {  "propagate": "True" }},"formatters": { "generic": {  "fmt": "{name}: {message}"}}}',
    )

    settings = Settings()

    configure_logging(config=settings.LOGGING_CONFIG)

    logger = logging.getLogger("tr")

    message = "This is a test log message with other formatting"
    logger.debug(message)
    logger.info(message)
    logger.warning(message)
    logger.error(message)
    logger.critical(message)

    assert len(caplog.records) == 4


def test_logging_loglevel(caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch):
    config = {"loggers": {"tr": {"propagate": True}}}

    configure_logging(config=config)

    monkeypatch.setenv("LOGGING_LEVEL", "ERROR")

    settings = Settings()

    configure_logging(config=config, level=settings.LOGGING_LEVEL)

    logger = logging.getLogger("tr.main")

    message = "This is a test log message with different logging level"
    logger.debug(message)
    logger.info(message)
    logger.warning(message)
    logger.error(message)
    logger.critical(message)

    assert len(caplog.records) == 2
