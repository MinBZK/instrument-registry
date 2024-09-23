import logging
from collections.abc import Generator
from unittest.mock import mock_open, patch

import pytest
from fastapi.testclient import TestClient
from task_registry.server import create_app

logger = logging.getLogger(__name__)


@pytest.fixture
def _mock_open_file() -> Generator[None, None, None]:  # type: ignore
    with patch("builtins.open", mock_open(read_data="{'urn':'test_urn'}")):
        yield


@pytest.fixture
def client(
    monkeypatch: pytest.MonkeyPatch, _mock_open_file: Generator[None, None, None]
) -> Generator[TestClient, None, None]:
    app = create_app()

    with TestClient(app, raise_server_exceptions=True) as c:
        c.timeout = 5
        yield c
