import subprocess

import pytest

from instrument_registry import __main__
from instrument_registry.validate import ValidationError


def test_main_process():
    completed_process = subprocess.run(["python", "-m", "instrument_registry"], capture_output=True, text=True)
    assert completed_process.returncode == 0


def test_main_function():
    assert __main__.main() == 0


def test_main_reports_errors_and_returns_nonzero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        __main__,
        "validate_all",
        lambda: [ValidationError(file="dpia.yaml", message="'urn' is a required property")],
    )

    assert __main__.main() == 1
    assert "dpia.yaml: 'urn' is a required property" in capsys.readouterr().err
