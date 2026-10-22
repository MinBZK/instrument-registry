from pathlib import Path

import pytest

from instrument_registry import release


def test_project_version_comes_from_pyproject() -> None:
    assert release.project_version() == "0.1.0"


def test_project_version_reads_the_given_file(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[tool.poetry]\nversion = "2.3.4"\n')

    assert release.project_version(pyproject) == "2.3.4"


def test_matching_tag_passes() -> None:
    assert release.check_tag("v0.1.0", "0.1.0") is None


@pytest.mark.parametrize("tag", ["0.1.0", "v0.1.1", "v0.1", "release-0.1.0"])
def test_mismatching_tag_is_reported(tag: str) -> None:
    problem = release.check_tag(tag, "0.1.0")

    assert problem is not None
    assert "verwacht v0.1.0" in problem


def test_main_accepts_the_current_version() -> None:
    assert release.main([f"v{release.project_version()}"]) == 0


def test_main_rejects_another_version(capsys: pytest.CaptureFixture[str]) -> None:
    assert release.main(["v99.0.0"]) == 1
    assert "past niet bij pyproject.toml" in capsys.readouterr().err


def test_main_requires_exactly_one_tag(capsys: pytest.CaptureFixture[str]) -> None:
    assert release.main([]) == 2
    assert "gebruik:" in capsys.readouterr().err
