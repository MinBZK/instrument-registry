from fastapi.testclient import TestClient


def test_get_main_page(client: TestClient) -> None:
    # when
    response = client.get("/instruments/")

    # then
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert b'{"type":"dir","size":0,"name":"instruments","path":"instruments"' in response.content.lower()
