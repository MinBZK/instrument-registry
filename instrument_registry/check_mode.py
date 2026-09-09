"""CI-poort: bewaakt dat de inhoud alleen langs het toegestane pad wijzigt."""

import subprocess
import sys

from instrument_registry.mode import check_manual_edits, load_mode


def changed_files(base_ref: str) -> list[str]:
    """List the files a branch changes relative to its base."""
    output = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in output.stdout.splitlines() if line]


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - bedraad in de workflow
    argv = sys.argv[1:] if argv is None else argv
    base_ref = argv[0] if argv else "origin/main"
    mode = load_mode()
    violations = check_manual_edits(mode, changed_files(base_ref))
    if not violations:
        return 0
    print(
        "De registry staat in mirror-stand: de inhoud komt van MinBZK/par-dpia-form en wordt\n"
        "uitsluitend door de sync-workflow bijgewerkt. Dien deze wijziging daar in.\n"
        "Handmatig gewijzigd:",
        file=sys.stderr,
    )
    for path in violations:
        print(f"  {path}", file=sys.stderr)
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
