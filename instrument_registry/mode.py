"""Wie de inhoud van de registry mag schrijven.

In mirror-stand komt de inhoud uitsluitend van de sync-workflow; handmatige
wijzigingen horen dan upstream thuis. In authoritative-stand leeft de bron hier
en is een pull request op deze repo het normale pad.
"""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY_FILE = ROOT / "registry.toml"

MODES = ("mirror", "authoritative")
CONTENT_PATHS = ("assessments/", "schemas/")


def load_mode() -> str:
    """Read the declared mode from registry.toml."""
    with REGISTRY_FILE.open("rb") as handle:
        settings = tomllib.load(handle)
    mode: str = settings["content"]["mode"]
    return mode


def check_manual_edits(mode: str, changed_files: list[str]) -> list[str]:
    """Return the changed files that this mode does not allow a human to touch."""
    if mode not in MODES:
        raise ValueError(f"onbekende mode: {mode}")
    if mode == "authoritative":
        return []
    return [path for path in changed_files if path.startswith(CONTENT_PATHS)]
