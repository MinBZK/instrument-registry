import json
from pathlib import Path

import pytest

from instrument_registry import sync


def fake_upstream(contents: dict[str, bytes]) -> sync.Fetcher:
    def fetch(path: str) -> bytes:
        return contents[path]

    return fetch


def test_sync_writes_upstream_content(tmp_path: Path) -> None:
    fetch = fake_upstream({"sources/dpia.yaml": b"naam: DPIA\n"})

    changed = sync.sync_files({"sources/dpia.yaml": "assessments/dpia.yaml"}, fetch, tmp_path)

    assert changed == ["assessments/dpia.yaml"]
    assert (tmp_path / "assessments/dpia.yaml").read_bytes() == b"naam: DPIA\n"


def test_sync_reports_nothing_when_content_is_identical(tmp_path: Path) -> None:
    target = tmp_path / "assessments/dpia.yaml"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"naam: DPIA\n")
    fetch = fake_upstream({"sources/dpia.yaml": b"naam: DPIA\n"})

    assert sync.sync_files({"sources/dpia.yaml": "assessments/dpia.yaml"}, fetch, tmp_path) == []


def test_provenance_records_the_upstream_commit(tmp_path: Path) -> None:
    sync.write_provenance(
        tmp_path, repo="MinBZK/par-dpia-form", ref="main", sha="abc123", files=["assessments/dpia.yaml"]
    )

    provenance = json.loads((tmp_path / "assessments/PROVENANCE.json").read_text())

    assert provenance["repo"] == "MinBZK/par-dpia-form"
    assert provenance["ref"] == "main"
    assert provenance["sha"] == "abc123"
    assert provenance["files"] == ["assessments/dpia.yaml"]
    assert provenance["synced_at"].endswith("Z")


def test_sync_refuses_to_run_in_authoritative_mode(tmp_path: Path) -> None:
    with pytest.raises(sync.SyncNotAllowed):
        sync.guard_mode("authoritative")


def test_sync_runs_in_mirror_mode() -> None:
    sync.guard_mode("mirror")


def test_upstream_settings_come_from_registry_toml() -> None:
    repo, ref, files = sync.load_upstream()

    assert repo == "MinBZK/par-dpia-form"
    assert ref == "main"
    assert files["sources/dpia.yaml"] == "assessments/dpia.yaml"


class FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return self.payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_github_fetcher_reads_raw_content(monkeypatch: pytest.MonkeyPatch) -> None:
    urls: list[str] = []

    def fake_urlopen(url: str) -> FakeResponse:
        urls.append(url)
        return FakeResponse(b"naam: DPIA\n")

    monkeypatch.setattr(sync.urllib.request, "urlopen", fake_urlopen)

    content = sync.github_fetcher("MinBZK/par-dpia-form", "main")("sources/dpia.yaml")

    assert content == b"naam: DPIA\n"
    assert urls == ["https://raw.githubusercontent.com/MinBZK/par-dpia-form/main/sources/dpia.yaml"]


def test_resolve_sha_reads_the_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sync.urllib.request,
        "urlopen",
        lambda url: FakeResponse(b'{"sha": "abc123"}'),
    )

    assert sync.resolve_sha("MinBZK/par-dpia-form", "main") == "abc123"
