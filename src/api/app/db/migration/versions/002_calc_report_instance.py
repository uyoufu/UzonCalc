"""
Add calculation report instances

Revision ID: 002_calc_report_instance
Revises: 001_initial_schema
Create Date: 2026-05-11
"""

from alembic import op
import sqlalchemy as sa

revision = "002_calc_report_instance"
down_revision = "001_initial_schema"
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
    """创建计算实例和实例分类表。"""
    op.create_table(
        "calc_report_instance_category",
        sa.Column("userId", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("status", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        *_base_columns(),
    )
    _create_base_indexes("calc_report_instance_category")
    op.create_index(
        "ix_calc_report_instance_category_userId",
        "calc_report_instance_category",
        ["userId"],
    )
    op.create_index(
        "ix_calc_report_instance_category_name",
        "calc_report_instance_category",
        ["name"],
    )

    op.create_table(
        "calc_report_instance",
        sa.Column("userId", sa.Integer(), nullable=False),
        sa.Column("categoryId", sa.Integer(), nullable=False),
        sa.Column("reportId", sa.Integer(), nullable=False),
        sa.Column("reportName", sa.String(length=100), nullable=True),
        sa.Column("status", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("defaults", sa.JSON(), nullable=False),
        sa.Column("resultPath", sa.String(length=500), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("lastModified", sa.DateTime(timezone=True), nullable=False),
        *_base_columns(),
    )
    _create_base_indexes("calc_report_instance")
    op.create_index("ix_calc_report_instance_userId", "calc_report_instance", ["userId"])
    op.create_index(
        "ix_calc_report_instance_categoryId", "calc_report_instance", ["categoryId"]
    )
    op.create_index(
        "ix_calc_report_instance_reportId", "calc_report_instance", ["reportId"]
    )
    op.create_index(
        "ix_calc_report_instance_lastModified",
        "calc_report_instance",
        ["lastModified"],
    )


def downgrade() -> None:
    """删除计算实例和实例分类表。"""
    op.drop_index("ix_calc_report_instance_lastModified", table_name="calc_report_instance")
    op.drop_index("ix_calc_report_instance_reportId", table_name="calc_report_instance")
    op.drop_index("ix_calc_report_instance_categoryId", table_name="calc_report_instance")
    op.drop_index("ix_calc_report_instance_userId", table_name="calc_report_instance")
    _drop_base_indexes("calc_report_instance")
    op.drop_table("calc_report_instance")

    op.drop_index(
        "ix_calc_report_instance_category_name",
        table_name="calc_report_instance_category",
    )
    op.drop_index(
        "ix_calc_report_instance_category_userId",
        table_name="calc_report_instance_category",
    )
    _drop_base_indexes("calc_report_instance_category")
    op.drop_table("calc_report_instance_category")
