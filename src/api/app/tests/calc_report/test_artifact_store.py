"""Tests for content-addressed calculation-report artifacts."""

import json
from pathlib import Path

import pytest

from app.service.calc_report_artifact_service import (
    ArtifactFile,
    ArtifactStore,
    ArtifactValidationError,
)


def _workspace_files(main_source: bytes = b"x = 1\n") -> list[ArtifactFile]:
    """Build a minimal valid workspace fixture."""
    calcbook = json.dumps({"formatVersion": 1, "entryPath": "src/main.py"}).encode()
    return [
        ArtifactFile("calcbook.json", calcbook),
        ArtifactFile("src/main.py", main_source),
        ArtifactFile("resources/logo.bin", b"\x00\x01"),
    ]


def test_source_artifact_hash_is_independent_of_input_order(tmp_path: Path) -> None:
    """Equivalent complete workspaces should reuse one deterministic artifact."""
    store = ArtifactStore(tmp_path / "artifacts")
    calcbook = {"formatVersion": 1, "entryPath": "src/main.py"}

    first = store.publish_source(_workspace_files(), calcbook, [])
    second = store.publish_source(reversed(_workspace_files()), calcbook, [])

    assert first.content_hash == second.content_hash
    assert first.storage_key == second.storage_key
    assert store.read_file(first.storage_key, "resources/logo.bin") == b"\x00\x01"


def test_source_artifact_hash_includes_dependencies(tmp_path: Path) -> None:
    """Changing dependency declarations must invalidate a SOURCE artifact."""
    store = ArtifactStore(tmp_path / "artifacts")
    calcbook = {"formatVersion": 1, "entryPath": "src/main.py"}

    without_dependency = store.publish_source(_workspace_files(), calcbook, [])
    with_dependency = store.publish_source(
        _workspace_files(),
        calcbook,
        [{"alias": "beam", "targetReportOid": "a" * 24, "selectors": []}],
    )

    assert without_dependency.content_hash != with_dependency.content_hash


def test_artifact_store_rejects_unsafe_or_duplicate_paths(tmp_path: Path) -> None:
    """Workspace publication should reject traversal and duplicate files."""
    store = ArtifactStore(tmp_path / "artifacts")
    calcbook = {"formatVersion": 1, "entryPath": "src/main.py"}

    with pytest.raises(ArtifactValidationError):
        store.publish_source(
            _workspace_files() + [ArtifactFile("../secret", b"x")], calcbook, []
        )
    with pytest.raises(ArtifactValidationError):
        store.publish_source(
            _workspace_files() + [ArtifactFile("src/main.py", b"x")], calcbook, []
        )


def test_materialize_atomically_replaces_projection(tmp_path: Path) -> None:
    """Materialization should replace stale projection files as a whole."""
    store = ArtifactStore(tmp_path / "artifacts")
    artifact = store.publish_source(
        _workspace_files(), {"formatVersion": 1, "entryPath": "src/main.py"}, []
    )
    target = tmp_path / "workspace"
    target.mkdir()
    (target / "stale.txt").write_text("stale")

    store.materialize(artifact.storage_key, target)

    assert not (target / "stale.txt").exists()
    assert (target / "src/main.py").read_bytes() == b"x = 1\n"
