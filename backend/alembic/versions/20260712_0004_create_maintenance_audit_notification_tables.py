"""create maintenance audit notification tables

Revision ID: 20260712_0004
Revises: 2712b6b1ff2c
Create Date: 2026-07-12 16:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260712_0004"
down_revision: Union[str, None] = "2712b6b1ff2c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "maintenance_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("preferred_date", sa.Date(), nullable=True),
        sa.Column("technician_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("estimated_cost", sa.Numeric(), nullable=True),
        sa.Column("actual_cost", sa.Numeric(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.CheckConstraint("priority IN ('low','medium','high','critical')", name="ck_maintenance_requests_priority"),
        sa.CheckConstraint(
            "status IN ('pending','approved','rejected','assigned','in_progress','resolved')",
            name="ck_maintenance_requests_status",
        ),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["requested_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["technician_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_maintenance_requests_asset_id"), "maintenance_requests", ["asset_id"])
    op.create_index(op.f("ix_maintenance_requests_code"), "maintenance_requests", ["code"], unique=True)
    op.create_index(op.f("ix_maintenance_requests_requested_by_id"), "maintenance_requests", ["requested_by_id"])
    op.create_index(op.f("ix_maintenance_requests_status"), "maintenance_requests", ["status"])

    op.create_table(
        "maintenance_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["request_id"], ["maintenance_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_maintenance_history_by_id"), "maintenance_history", ["by_id"])
    op.create_index(op.f("ix_maintenance_history_request_id"), "maintenance_history", ["request_id"])

    op.create_table(
        "audit_cycles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("scope_department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scope_location", sa.String(120), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint("end_date >= start_date", name="ck_audit_cycles_date_order"),
        sa.CheckConstraint("status IN ('draft','active','in_review','closed')", name="ck_audit_cycles_status"),
        sa.ForeignKeyConstraint(["scope_department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_cycles_scope_department_id"), "audit_cycles", ["scope_department_id"])
    op.create_index(op.f("ix_audit_cycles_status"), "audit_cycles", ["status"])

    op.create_table(
        "audit_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("audit_cycle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("auditor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["audit_cycle_id"], ["audit_cycles.id"]),
        sa.ForeignKeyConstraint(["auditor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("audit_cycle_id", "auditor_id", name="uq_audit_assignments_cycle_auditor"),
    )
    op.create_index(op.f("ix_audit_assignments_audit_cycle_id"), "audit_assignments", ["audit_cycle_id"])
    op.create_index(op.f("ix_audit_assignments_auditor_id"), "audit_assignments", ["auditor_id"])

    op.create_table(
        "audit_findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("audit_cycle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("auditor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('pending','verified','missing','damaged')", name="ck_audit_findings_status"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["audit_cycle_id"], ["audit_cycles.id"]),
        sa.ForeignKeyConstraint(["auditor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("audit_cycle_id", "asset_id", name="uq_audit_findings_cycle_asset"),
    )
    op.create_index(op.f("ix_audit_findings_asset_id"), "audit_findings", ["asset_id"])
    op.create_index(op.f("ix_audit_findings_audit_cycle_id"), "audit_findings", ["audit_cycle_id"])
    op.create_index(op.f("ix_audit_findings_status"), "audit_findings", ["status"])

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("read", sa.Boolean(), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("link", sa.String(255), nullable=True),
        sa.CheckConstraint(
            "type IN ('allocation','transfer','maintenance','booking','audit','overdue')",
            name="ck_notifications_type",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notifications_user_id"), "notifications", ["user_id"])
    op.create_index("ix_notifications_user_read_at", "notifications", ["user_id", "read", "at"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_read_at", table_name="notifications")
    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_table("notifications")
    op.drop_index(op.f("ix_audit_findings_status"), table_name="audit_findings")
    op.drop_index(op.f("ix_audit_findings_audit_cycle_id"), table_name="audit_findings")
    op.drop_index(op.f("ix_audit_findings_asset_id"), table_name="audit_findings")
    op.drop_table("audit_findings")
    op.drop_index(op.f("ix_audit_assignments_auditor_id"), table_name="audit_assignments")
    op.drop_index(op.f("ix_audit_assignments_audit_cycle_id"), table_name="audit_assignments")
    op.drop_table("audit_assignments")
    op.drop_index(op.f("ix_audit_cycles_status"), table_name="audit_cycles")
    op.drop_index(op.f("ix_audit_cycles_scope_department_id"), table_name="audit_cycles")
    op.drop_table("audit_cycles")
    op.drop_index(op.f("ix_maintenance_history_request_id"), table_name="maintenance_history")
    op.drop_index(op.f("ix_maintenance_history_by_id"), table_name="maintenance_history")
    op.drop_table("maintenance_history")
    op.drop_index(op.f("ix_maintenance_requests_status"), table_name="maintenance_requests")
    op.drop_index(op.f("ix_maintenance_requests_requested_by_id"), table_name="maintenance_requests")
    op.drop_index(op.f("ix_maintenance_requests_code"), table_name="maintenance_requests")
    op.drop_index(op.f("ix_maintenance_requests_asset_id"), table_name="maintenance_requests")
    op.drop_table("maintenance_requests")
