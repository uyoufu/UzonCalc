"""Regression tests for isolated Ruff source formatting."""

import asyncio

import pytest

from app.controller.calc.code_format_dto import PythonRuffFormatReqDTO
from app.exception.custom_exception import CustomException
from app.service.code_format_service import format_python_with_ruff


def test_ruff_formatter_formats_source_and_reports_changes() -> None:
    """Ruff should format valid source and identify already formatted input."""

    async def run_test() -> None:
        """Run both formatter states in one event loop."""
        changed = await format_python_with_ruff(
            PythonRuffFormatReqDTO(code="value={'a':1}\n")
        )
        unchanged = await format_python_with_ruff(
            PythonRuffFormatReqDTO(code=changed.formattedCode)
        )

        assert changed.formatter == "ruff"
        assert changed.changed is True
        assert changed.formattedCode == 'value = {"a": 1}\n'
        assert unchanged.changed is False

    asyncio.run(run_test())


def test_ruff_formatter_rejects_invalid_python() -> None:
    """Ruff parse failures should remain a bounded HTTP 400 business error."""

    async def run_test() -> None:
        """Submit invalid Python and inspect the translated service error."""
        with pytest.raises(CustomException) as error:
            await format_python_with_ruff(PythonRuffFormatReqDTO(code="def broken(:\n"))

        assert error.value.code == 400
        assert "Ruff" in error.value.message

    asyncio.run(run_test())
