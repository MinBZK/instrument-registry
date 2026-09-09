import pytest
from fastapi.testclient import TestClient

from instrument_registry.api import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_assessments_index_lists_the_instruments(client: TestClient) -> None:
    index = client.get("/assessments").json()

    urns = {entry["urn"] for entry in index["entries"]}
    assert urns == {"urn:nl:dpia", "urn:nl:iama", "urn:nl:prescan"}


def test_index_entry_follows_the_task_registry_shape(client: TestClient) -> None:
    entry = client.get("/assessments").json()["entries"][0]

    assert set(entry) == {"type", "size", "name", "path", "urn", "download_url", "links"}
    assert entry["type"] == "file"
    assert entry["links"]["self"] == entry["download_url"]


def test_index_names_the_registry_version(client: TestClient) -> None:
    assert client.get("/assessments").json()["registry_version"]


def test_document_can_be_fetched_by_urn(client: TestClient) -> None:
    document = client.get("/assessments/urn/urn:nl:dpia").json()

    assert document["urn"] == "urn:nl:dpia"
    assert document["name"] == "DPIA Rapportagemodel Rijksdienst"


def test_download_url_from_the_index_resolves(client: TestClient) -> None:
    entry = client.get("/assessments").json()["entries"][0]

    response = client.get(entry["download_url"].replace("http://testserver", ""))

    assert response.status_code == 200


def test_yaml_is_served_byte_identical(client: TestClient) -> None:
    response = client.get("/assessments/urn/urn:nl:dpia", params={"format": "yaml"})

    assert response.headers["content-type"].startswith("application/yaml")
    assert response.text == (client.app.state.root / "assessments/dpia.yaml").read_text()  # type: ignore[attr-defined]


def test_unknown_urn_returns_404(client: TestClient) -> None:
    assert client.get("/assessments/urn/urn:nl:bestaatniet").status_code == 404


def test_begrippenkaders_are_served(client: TestClient) -> None:
    index = client.get("/begrippenkaders").json()

    assert {entry["name"] for entry in index["entries"]} == {
        "begrippenkader_dpia.yaml",
        "begrippenkader_iama.yaml",
    }


def test_schemas_are_served_by_name(client: TestClient) -> None:
    schema = client.get("/schemas/begrippenkader.v1.schema.json").json()

    assert schema["title"] == "Begrippenkader"


def test_responses_carry_a_stable_etag(client: TestClient) -> None:
    first = client.get("/assessments/urn/urn:nl:dpia")
    second = client.get("/assessments/urn/urn:nl:dpia")

    assert first.headers["etag"]
    assert first.headers["etag"] == second.headers["etag"]


def test_known_etag_yields_not_modified(client: TestClient) -> None:
    etag = client.get("/assessments/urn/urn:nl:dpia").headers["etag"]

    response = client.get("/assessments/urn/urn:nl:dpia", headers={"If-None-Match": etag})

    assert response.status_code == 304


def test_cross_origin_requests_are_allowed(client: TestClient) -> None:
    response = client.get("/assessments", headers={"Origin": "https://example.org"})

    assert response.headers["access-control-allow-origin"] == "*"


def test_begrippenkader_can_be_fetched_by_urn(client: TestClient) -> None:
    document = client.get("/begrippenkaders/urn/urn:nl:begrippenkaderdpia_pre-scandpia:3.0:begrippenkader:1.0.0")

    assert document.status_code == 200
    assert document.json()["name"].startswith("Begrippenkader")


def test_accept_header_selects_yaml(client: TestClient) -> None:
    response = client.get("/assessments/urn/urn:nl:iama", headers={"Accept": "application/yaml"})

    assert response.headers["content-type"].startswith("application/yaml")


def test_unknown_schema_returns_404(client: TestClient) -> None:
    assert client.get("/schemas/bestaat-niet.schema.json").status_code == 404


def test_schemas_index_lists_every_schema(client: TestClient) -> None:
    names = {entry["name"] for entry in client.get("/schemas").json()["entries"]}

    assert "assessment-definition.v2.schema.json" in names


def test_head_request_is_answered(client: TestClient) -> None:
    response = client.head("/assessments/urn/urn:nl:dpia")

    assert response.status_code == 200
    assert response.headers["etag"]
