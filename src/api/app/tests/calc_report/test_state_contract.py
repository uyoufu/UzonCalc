"""Tests for calculation-report string state contracts."""

from enum import StrEnum

import pytest
from pydantic import TypeAdapter, ValidationError

from app.controller.calc.calc_execution_dto import CalcExecutionSourceDTO
from app.controller.calc.calc_report_dto import CalcReportVersionReviewDTO
from app.controller.calc.calc_share_dto import ShareLinkCreateDTO
from app.controller.calc.calc_state import (
    BuildStatus,
    ExecutionSourceType,
    ExecutionStatus,
    ExecutorType,
    PublishState,
    ReviewStatus,
    ShareAccessType,
    WorkspaceFileSource,
)
from app.controller.calc.calc_workspace_dto import WorkspaceFileDTO


@pytest.mark.parametrize(
    ("enum_type", "expected_values"),
    [
        (
            PublishState,
            [
                "unpublished",
                "published",
                "unpublished_changes",
                "workspace_version_mismatch",
            ],
        ),
        (BuildStatus, ["not_requested", "pending", "building", "ready", "failed"]),
        (ReviewStatus, ["pending", "approved", "rejected"]),
        (ExecutionSourceType, ["workspace", "latest", "version"]),
        (
            ExecutionStatus,
            ["pending", "running", "succeeded", "failed", "cancelled", "expired"],
        ),
        (ShareAccessType, ["link", "public", "specified_users"]),
        (WorkspaceFileSource, ["upload", "current"]),
        (ExecutorType, ["local", "docker"]),
    ],
)
def test_state_enum_schema_exposes_stable_wire_values(
    enum_type: type[StrEnum], expected_values: list[str]
) -> None:
    """Expose every supported state as an OpenAPI-compatible enum.

    Args:
        enum_type: Public string enum being inspected.
        expected_values: Ordered wire values required by the API contract.

    Returns:
        None.

    Raises:
        AssertionError: If the generated schema changes the public values.
    """
    assert TypeAdapter(enum_type).json_schema()["enum"] == expected_values


def test_state_dtos_serialize_enum_values_as_existing_strings() -> None:
    """Serialize typed request values without changing their JSON representation.

    Returns:
        None.

    Raises:
        AssertionError: If a DTO emits an enum member name instead of its value.
    """
    source = CalcExecutionSourceDTO(
        type=ExecutionSourceType.VERSION, versionName="1.2.3"
    )
    review = CalcReportVersionReviewDTO(reviewStatus=ReviewStatus.APPROVED)
    share = ShareLinkCreateDTO(versionName="1.2.3")
    workspace_file = WorkspaceFileDTO(path="src/main.py")

    assert source.model_dump(mode="json") == {
        "type": "version",
        "versionName": "1.2.3",
    }
    assert review.model_dump(mode="json")["reviewStatus"] == "approved"
    assert share.model_dump(mode="json")["accessType"] == "link"
    assert workspace_file.model_dump(mode="json")["source"] == "upload"


@pytest.mark.parametrize(
    "factory",
    [
        lambda: CalcExecutionSourceDTO(type="retired"),
        lambda: CalcReportVersionReviewDTO(reviewStatus="retired"),
        lambda: ShareLinkCreateDTO(versionName="1.2.3", accessType="retired"),
        lambda: WorkspaceFileDTO(path="src/main.py", source="retired"),
    ],
)
def test_state_dtos_reject_unknown_values(factory) -> None:
    """Reject arbitrary strings at the public DTO boundary.

    Args:
        factory: Zero-argument DTO constructor containing an invalid state.

    Returns:
        None.

    Raises:
        AssertionError: If Pydantic accepts the invalid state.
    """
    with pytest.raises(ValidationError):
        factory()
