"""Haalt de instrumenten op bij de upstream-bron zolang de registry spiegelt.

De sync schrijft alleen bestanden; het openen van de pull request en het
beoordelen ervan gebeurt in de workflow. Zo blijft het verschil tussen upstream
en registry altijd zichtbaar voor een mens voordat het gepubliceerd wordt.
"""

import json
import tomllib
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from instrument_registry.mode import REGISTRY_FILE, ROOT

Fetcher = Callable[[str], bytes]

GITHUB_RAW = "https://raw.githubusercontent.com/{repo}/{ref}/{path}"
GITHUB_COMMIT = "https://api.github.com/repos/{repo}/commits/{ref}"


class SyncNotAllowed(Exception):
    """Raised when syncing would overwrite content this repository owns itself."""


def guard_mode(mode: str) -> None:
    """Refuse to sync once the registry owns its own content."""
    if mode != "mirror":
        raise SyncNotAllowed(f"sync hoort niet te draaien in mode {mode}")


def load_upstream() -> tuple[str, str, dict[str, str]]:
    """Read repo, ref and the file mapping from registry.toml."""
    with REGISTRY_FILE.open("rb") as handle:
        settings = tomllib.load(handle)
    upstream = settings["content"]["upstream"]
    repo: str = upstream["repo"]
    ref: str = upstream["ref"]
    files: dict[str, str] = upstream["files"]
    return repo, ref, files


def github_fetcher(repo: str, ref: str) -> Fetcher:
    """Fetch raw file content from a GitHub repository at a given ref."""

    def fetch(path: str) -> bytes:
        url = GITHUB_RAW.format(repo=repo, ref=ref, path=path)
        with urllib.request.urlopen(url) as response:  # noqa: S310 - vaste https-host
            content: bytes = response.read()
            return content

    return fetch


def resolve_sha(repo: str, ref: str) -> str:
    """Look up the commit a ref currently points at."""
    url = GITHUB_COMMIT.format(repo=repo, ref=ref)
    with urllib.request.urlopen(url) as response:  # noqa: S310 - vaste https-host
        commit: dict[str, object] = json.loads(response.read())
    sha = commit["sha"]
    return str(sha)


def sync_files(files: dict[str, str], fetch: Fetcher, root: Path) -> list[str]:
    """Write upstream content into the registry, returning the paths that changed."""
    changed: list[str] = []
    for upstream_path, registry_path in files.items():
        content = fetch(upstream_path)
        target = root / registry_path
        if target.exists() and target.read_bytes() == content:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        changed.append(registry_path)
    return changed


def write_provenance(root: Path, repo: str, ref: str, sha: str, files: list[str]) -> None:
    """Record which upstream commit the current content came from."""
    provenance = {
        "repo": repo,
        "ref": ref,
        "sha": sha,
        "synced_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "files": files,
    }
    target = root / "assessments/PROVENANCE.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n")


def main() -> int:  # pragma: no cover - bedraad in de workflow
    from instrument_registry.mode import load_mode

    guard_mode(load_mode())
    repo, ref, files = load_upstream()
    sha = resolve_sha(repo, ref)
    changed = sync_files(files, github_fetcher(repo, ref), ROOT)
    if changed:
        write_provenance(ROOT, repo=repo, ref=ref, sha=sha, files=sorted(files.values()))
    for path in changed:
        print(path)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
