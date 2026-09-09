import subprocess
from pathlib import Path

from instrument_registry import check_mode


def git(repository: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repository, check=True, capture_output=True)


def test_changed_files_lists_what_a_branch_touches(tmp_path: Path, monkeypatch) -> None:
    git(tmp_path, "init", "--initial-branch=main")
    git(tmp_path, "config", "user.email", "test@example.org")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "README.md").write_text("start\n")
    git(tmp_path, "add", "README.md")
    git(tmp_path, "commit", "-m", "start")
    git(tmp_path, "checkout", "-b", "wijziging")
    (tmp_path / "assessments").mkdir()
    (tmp_path / "assessments/dpia.yaml").write_text("naam: DPIA\n")
    git(tmp_path, "add", "assessments/dpia.yaml")
    git(tmp_path, "commit", "-m", "voeg toe")
    monkeypatch.chdir(tmp_path)

    assert check_mode.changed_files("main") == ["assessments/dpia.yaml"]
