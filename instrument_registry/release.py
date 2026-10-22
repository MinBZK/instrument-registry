"""Koppelt de versie van de registry aan de GitHub-release.

De release-tag (`v0.1.0`) is wat afnemers zien, in de image-tag en in
`registry_version` van elke index. pyproject.toml noemt dezelfde versie zonder
`v`; de release-workflow weigert te bouwen als die twee uiteenlopen.
"""

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT_FILE = ROOT / "pyproject.toml"


def project_version(pyproject: Path = PYPROJECT_FILE) -> str:
    """Read the version pyproject.toml declares."""
    with pyproject.open("rb") as handle:
        settings = tomllib.load(handle)
    version: str = settings["tool"]["poetry"]["version"]
    return version


def check_tag(tag: str, version: str) -> str | None:
    """Return why a release tag does not fit the project version, or None when it does."""
    expected = f"v{version}"
    if tag != expected:
        return f"release-tag {tag} past niet bij pyproject.toml (versie {version}); verwacht {expected}"
    return None


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("gebruik: python -m instrument_registry.release <release-tag>", file=sys.stderr)
        return 2
    problem = check_tag(argv[0], project_version())
    if problem:
        print(problem, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
