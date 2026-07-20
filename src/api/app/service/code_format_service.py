"""Server-side source formatting services."""

import asyncio
import sys

from app.controller.calc.code_format_dto import (
    PythonRuffFormatReqDTO,
    PythonRuffFormatResDTO,
)
from app.exception.custom_exception import raise_ex
from app.i18n import _


async def format_python_with_ruff(
    data: PythonRuffFormatReqDTO,
) -> PythonRuffFormatResDTO:
    """Format untrusted Python source with Ruff in an isolated subprocess.

    Args:
        data: Source text and positive target line length.

    Returns:
        Formatted source and a changed flag.

    Raises:
        CustomException: If validation fails, Ruff rejects the source, or the
            formatter process cannot complete successfully.
    """
    line_length = data.lineLength
    if line_length <= 0:
        raise_ex("lineLength must be greater than 0", code=400)
    try:
        formatter = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "ruff",
            "format",
            "--isolated",
            "--line-length",
            str(line_length),
            "--stdin-filename",
            "workspace.py",
            "-",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await formatter.communicate(data.code.encode("utf-8"))
    except OSError:
        raise_ex(_("Python formatter is unavailable"), code=500)
    if formatter.returncode != 0:
        message = stderr.decode("utf-8", errors="replace").strip()
        raise_ex(
            _("Ruff format failed: {error}").format(error=message),
            code=400,
        )
    formatted_code = stdout.decode("utf-8")
    return PythonRuffFormatResDTO(
        formattedCode=formatted_code,
        changed=formatted_code != data.code,
    )
