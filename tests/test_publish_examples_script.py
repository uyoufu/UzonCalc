from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLISH_SCRIPT = REPO_ROOT / "scripts/publish-examples.ps1"


def test_publish_examples_script_recurses_and_renders_to_temp_directory():
    """示例发布脚本应递归生成计算书 HTML 到临时目录后再发布。"""
    script = PUBLISH_SCRIPT.read_text("utf-8")

    assert "-Recurse" in script
    assert "ast.parse" in script
    assert "ast.FunctionDef, ast.AsyncFunctionDef" in script
    assert "uv run --no-project python -c $checkScript $Path" in script
    assert "    python -c $checkScript $Path" not in script
    assert "uv run --project $projectRoot --package uzoncalc uzoncalc" in script
    assert "[System.IO.Path]::GetRelativePath" in script
    assert "[System.IO.Path]::GetTempPath()" in script
    assert "Remove-Item $tempRoot -Recurse -Force" in script
    assert 'Join-Path $publishOutputDir "$relativeBase.html"' in script
