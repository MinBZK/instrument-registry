import logging
from typing import Any

from task_registry import data

logger = logging.getLogger(__name__)

TEST_INDEX: dict[str, Any] = {
    "_links": {"self": "test.io/index.json"},
    "download_url": "test.io/index.json",
    "entries": [],
    "name": "test",
    "path": "test",
    "size": 0,
    "type": "dir",
}


def test_create_urn_mappper() -> None:
    urn_mapper = data.create_urn_mappper(entries=TEST_INDEX["entries"])
    assert urn_mapper == {}


def test_generate_index() -> None:
    index = data.generate_index(base_url="test.io", directory="test", output_file="index.json")
    assert index == TEST_INDEX
