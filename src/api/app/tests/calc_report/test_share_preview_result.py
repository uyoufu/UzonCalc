"""Regression tests for share-preview result file validation."""

from pathlib import Path

import pytest

from app.db.models.calc_execution import CalcExecution
from app.exception.custom_exception import CustomException
from app.service.calc_report_share_service import _existing_execution_result_path


def test_existing_execution_result_path_requires_a_real_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A stale database result path must not be reused after its HTML file disappears."""
    monkeypatch.chdir(tmp_path)
    execution = CalcExecution(resultPath="public/calcs/result.html")

    assert _existing_execution_result_path(execution) is None

    result_path = tmp_path / "data" / "public" / "calcs" / "result.html"
    result_path.parent.mkdir(parents=True)
    result_path.write_text("<html></html>", encoding="utf-8")

    assert _existing_execution_result_path(execution) == Path("data/public/calcs/result.html")


def test_existing_execution_result_path_rejects_directory_escape() -> None:
    """A persisted result path may not escape the application data directory."""
    execution = CalcExecution(resultPath="../outside.html")

    with pytest.raises(CustomException, match="path is invalid"):
        _existing_execution_result_path(execution)
