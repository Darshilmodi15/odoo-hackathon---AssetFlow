"""create assets table

Revision ID: 20260712_0002
Revises: 20260712_0001
Create Date: 2026-07-12 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
# pyrefly: ignore [missing-import]
import sqlalchemy as sa
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260712_0002"
down_revision: Union[str, None] = "20260712_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tag", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("serial_number", sa.String(length=120), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_to_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("location", sa.String(length=120), nullable=False),
        sa.Column("condition", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="available"),
        sa.Column("shared", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("acquisition_date", sa.Date(), nullable=False),
        sa.Column("acquisition_cost", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        # Primary key
        sa.PrimaryKeyConstraint("id"),
        # Foreign keys
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["asset_categories.id"],
            name="fk_assets_category_id_asset_categories",
        ),
        sa.ForeignKeyConstraint(
            ["department_id"],
            ["departments.id"],
            name="fk_assets_department_id_departments",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_to_id"],
            ["users.id"],
            name="fk_assets_assigned_to_id_users",
        ),
    )

    # Unique constraints
    op.create_index(op.f("ix_assets_tag"), "assets", ["tag"], unique=True)
    op.create_index(op.f("ix_assets_serial_number"), "assets", ["serial_number"], unique=True)

    # Non-unique indexes for filtering performance
    op.create_index("ix_assets_status", "assets", ["status"], unique=False)
    op.create_index("ix_assets_category_id", "assets", ["category_id"], unique=False)
    op.create_index("ix_assets_department_id", "assets", ["department_id"], unique=False)


def downgrade() -> None:
    # Drop indexes first
    op.drop_index("ix_assets_department_id", table_name="assets")
    op.drop_index("ix_assets_category_id", table_name="assets")
    op.drop_index("ix_assets_status", table_name="assets")
    op.drop_index(op.f("ix_assets_serial_number"), table_name="assets")
    op.drop_index(op.f("ix_assets_tag"), table_name="assets")

    # Drop the table (cascades FK constraints)
    op.drop_table("assets")
