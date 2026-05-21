"""
Initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-05-11
"""

from alembic import op
import sqlalchemy as sa

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def _base_columns() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("oid", sa.String(length=24), nullable=False),
        sa.Column("createdAt", sa.DateTime(timezone=True), nullable=False),
    ]


def _create_base_indexes(table_name: str) -> None:
    op.create_index(f"ix_{table_name}_id", table_name, ["id"])
    op.create_index(f"ix_{table_name}_oid", table_name, ["oid"])
    op.create_index(f"ix_{table_name}_createdAt", table_name, ["createdAt"])


def _drop_base_indexes(table_name: str) -> None:
    op.drop_index(f"ix_{table_name}_createdAt", table_name=table_name)
    op.drop_index(f"ix_{table_name}_oid", table_name=table_name)
    op.drop_index(f"ix_{table_name}_id", table_name=table_name)


def upgrade() -> None:
    """创建初始业务表。"""
    op.create_table(
        "users",
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=True),
        sa.Column("avatar", sa.String(length=255), nullable=True),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("salt", sa.String(length=255), nullable=False),
        sa.Column("status", sa.Integer(), nullable=False),
        sa.Column("roles", sa.JSON(), nullable=False),
        *_base_columns(),
        sa.UniqueConstraint("username"),
    )
    _create_base_indexes("users")
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_status", "users", ["status"])

    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("readonly", sa.Boolean(), nullable=False),
        *_base_columns(),
        sa.UniqueConstraint("key"),
    )
    _create_base_indexes("system_settings")
    op.create_index("ix_system_settings_key", "system_settings", ["key"])

    op.create_table(
        "user_settings",
        sa.Column("userId", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        *_base_columns(),
    )
    _create_base_indexes("user_settings")

    op.create_table(
        "calc_report_category",
        sa.Column("userId", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("status", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        *_base_columns(),
    )
    _create_base_indexes("calc_report_category")
    op.create_index(
        "ix_calc_report_category_userId", "calc_report_category", ["userId"]
    )
    op.create_index("ix_calc_report_category_name", "calc_report_category", ["name"])

    op.create_table(
        "calc_report",
        sa.Column("userId", sa.Integer(), nullable=False),
        sa.Column("categoryId", sa.Integer(), nullable=False),
        sa.Column("type", sa.Integer(), nullable=False),
        sa.Column("status", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover", sa.String(length=255), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("copyFromId", sa.Integer(), nullable=False),
        sa.Column("lastModified", sa.DateTime(timezone=True), nullable=False),
        sa.Column("isApproved", sa.Boolean(), nullable=False),
        sa.Column("shareType", sa.Integer(), nullable=False),
        sa.Column("shareToUserIds", sa.JSON(), nullable=True),
        *_base_columns(),
    )
    _create_base_indexes("calc_report")
    op.create_index("ix_calc_report_userId", "calc_report", ["userId"])
    op.create_index("ix_calc_report_categoryId", "calc_report", ["categoryId"])
    op.create_index("ix_calc_report_lastModified", "calc_report", ["lastModified"])

    op.create_table(
        "calc_report_archive",
        sa.Column("userId", sa.Integer(), nullable=False),
        sa.Column("status", sa.Integer(), nullable=False),
        sa.Column("type", sa.Integer(), nullable=False),
        sa.Column("reportId", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("defaults", sa.JSON(), nullable=False),
        *_base_columns(),
    )
    _create_base_indexes("calc_report_archive")
    op.create_index("ix_calc_report_archive_userId", "calc_report_archive", ["userId"])

    op.create_table(
        "tmp_files",
        sa.Column("filePath", sa.String(length=500), nullable=False),
        sa.Column("expireTime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("isDeleted", sa.Boolean(), nullable=False),
        sa.Column("deletedAt", sa.DateTime(timezone=True), nullable=True),
        *_base_columns(),
        sa.UniqueConstraint("filePath"),
    )
    _create_base_indexes("tmp_files")
    op.create_index("ix_tmp_files_filePath", "tmp_files", ["filePath"])
    op.create_index("ix_tmp_files_expireTime", "tmp_files", ["expireTime"])
    op.create_index("ix_tmp_files_isDeleted", "tmp_files", ["isDeleted"])

    op.create_table(
        "favorite_calc_reports",
        sa.Column("userId", sa.String(length=50), nullable=False),
        *_base_columns(),
    )
    _create_base_indexes("favorite_calc_reports")
    op.create_index(
        "ix_favorite_calc_reports_userId", "favorite_calc_reports", ["userId"]
    )

    op.create_table(
        "user_input_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("userId", sa.String(length=64), nullable=False),
        sa.Column("filePath", sa.String(length=256), nullable=False),
        sa.Column("funcName", sa.String(length=128), nullable=False),
        sa.Column("sessionId", sa.String(length=64), nullable=False),
        sa.Column("inputHistory", sa.JSON(), nullable=True),
        sa.Column("currentStep", sa.Integer(), nullable=True),
        sa.Column("totalSteps", sa.Integer(), nullable=True),
        sa.Column("finalResult", sa.Text(), nullable=True),
        sa.Column("finalResultHash", sa.String(length=64), nullable=True),
        sa.Column("isComplete", sa.Boolean(), nullable=True),
        sa.Column("isDraft", sa.Boolean(), nullable=True),
        sa.Column("draftVersionId", sa.Integer(), nullable=True),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("executionTime", sa.Integer(), nullable=True),
        sa.Column("errorMessage", sa.Text(), nullable=True),
        sa.Column("createdAt", sa.DateTime(), nullable=False),
        sa.Column("updatedAt", sa.DateTime(), nullable=False),
        sa.Column("completedAt", sa.DateTime(), nullable=True),
        sa.UniqueConstraint(
            "userId", "filePath", "funcName", "sessionId", name="uq_user_execution"
        ),
    )
    op.create_index(
        "idx_user_file_func", "user_input_history", ["userId", "filePath", "funcName"]
    )
    op.create_index(
        "idx_user_created_at", "user_input_history", ["userId", "createdAt"]
    )

    op.create_table(
        "published_version",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("userId", sa.String(length=64), nullable=False),
        sa.Column("filePath", sa.String(length=256), nullable=False),
        sa.Column("funcName", sa.String(length=128), nullable=False),
        sa.Column("versionName", sa.String(length=128), nullable=False),
        sa.Column("versionNumber", sa.Integer(), nullable=True),
        sa.Column("versionDescription", sa.Text(), nullable=True),
        sa.Column("inputHistory", sa.JSON(), nullable=False),
        sa.Column("finalResult", sa.Text(), nullable=False),
        sa.Column("finalResultHash", sa.String(length=64), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("totalSteps", sa.Integer(), nullable=False),
        sa.Column("executionTime", sa.Integer(), nullable=True),
        sa.Column("createdAt", sa.DateTime(), nullable=False),
        sa.Column("publishedAt", sa.DateTime(), nullable=False),
        sa.Column("createdFromHistoryId", sa.Integer(), nullable=True),
        sa.Column("downloadCount", sa.Integer(), nullable=True),
        sa.Column("useCount", sa.Integer(), nullable=True),
        sa.Column("isPublic", sa.Boolean(), nullable=True),
    )
    op.create_index(
        "idx_user_published", "published_version", ["userId", "publishedAt"]
    )
    op.create_index(
        "idx_file_version",
        "published_version",
        ["filePath", "funcName", "versionNumber"],
    )

    op.create_table(
        "input_cache",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("userId", sa.String(length=64), nullable=False),
        sa.Column("filePath", sa.String(length=256), nullable=False),
        sa.Column("funcName", sa.String(length=128), nullable=False),
        sa.Column("cachedInput", sa.JSON(), nullable=False),
        sa.Column("inputHistoryId", sa.Integer(), nullable=False),
        sa.Column("totalSteps", sa.Integer(), nullable=False),
        sa.Column("completedSteps", sa.Integer(), nullable=False),
        sa.Column("createdAt", sa.DateTime(), nullable=False),
        sa.Column("updatedAt", sa.DateTime(), nullable=False),
        sa.Column("expiresAt", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "idx_cache_user_file", "input_cache", ["userId", "filePath", "funcName"]
    )


def downgrade() -> None:
    """删除初始业务表。"""
    op.drop_index("idx_cache_user_file", table_name="input_cache")
    op.drop_table("input_cache")

    op.drop_index("idx_file_version", table_name="published_version")
    op.drop_index("idx_user_published", table_name="published_version")
    op.drop_table("published_version")

    op.drop_index("idx_user_created_at", table_name="user_input_history")
    op.drop_index("idx_user_file_func", table_name="user_input_history")
    op.drop_table("user_input_history")

    op.drop_index("ix_favorite_calc_reports_userId", table_name="favorite_calc_reports")
    _drop_base_indexes("favorite_calc_reports")
    op.drop_table("favorite_calc_reports")

    op.drop_index("ix_tmp_files_isDeleted", table_name="tmp_files")
    op.drop_index("ix_tmp_files_expireTime", table_name="tmp_files")
    op.drop_index("ix_tmp_files_filePath", table_name="tmp_files")
    _drop_base_indexes("tmp_files")
    op.drop_table("tmp_files")

    op.drop_index("ix_calc_report_archive_userId", table_name="calc_report_archive")
    _drop_base_indexes("calc_report_archive")
    op.drop_table("calc_report_archive")

    op.drop_index("ix_calc_report_lastModified", table_name="calc_report")
    op.drop_index("ix_calc_report_categoryId", table_name="calc_report")
    op.drop_index("ix_calc_report_userId", table_name="calc_report")
    _drop_base_indexes("calc_report")
    op.drop_table("calc_report")

    op.drop_index("ix_calc_report_category_name", table_name="calc_report_category")
    op.drop_index("ix_calc_report_category_userId", table_name="calc_report_category")
    _drop_base_indexes("calc_report_category")
    op.drop_table("calc_report_category")

    _drop_base_indexes("user_settings")
    op.drop_table("user_settings")

    op.drop_index("ix_system_settings_key", table_name="system_settings")
    _drop_base_indexes("system_settings")
    op.drop_table("system_settings")

    op.drop_index("ix_users_status", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    _drop_base_indexes("users")
    op.drop_table("users")
