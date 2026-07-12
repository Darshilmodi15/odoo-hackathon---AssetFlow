"""create asset workflow tables

Revision ID: 20260712_0003
Revises: 7086c3895342
Create Date: 2026-07-12 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260712_0003"
down_revision: Union[str, None] = "7086c3895342"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("allocated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expected_return_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("return_condition", sa.String(32), nullable=True),
        sa.Column("return_notes", sa.Text(), nullable=True),
        sa.Column("return_document_url", sa.String(500), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint("status IN ('active','returned','transferred','overdue')", name="ck_allocations_status"),
        sa.CheckConstraint("employee_id IS NOT NULL OR department_id IS NOT NULL", name="ck_allocations_target"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["employee_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_allocations_asset_id"), "allocations", ["asset_id"])
    op.create_index(op.f("ix_allocations_employee_id"), "allocations", ["employee_id"])
    op.create_index(op.f("ix_allocations_department_id"), "allocations", ["department_id"])
    op.create_index(op.f("ix_allocations_status"), "allocations", ["status"])
    op.create_index("uq_allocations_one_active_per_asset", "allocations", ["asset_id"], unique=True, postgresql_where=sa.text("status = 'active'"))

    op.create_table(
        "transfer_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("from_department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("to_employee_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("to_department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("requested_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("approver_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.CheckConstraint("status IN ('requested','approved','rejected','completed')", name="ck_transfer_requests_status"),
        sa.CheckConstraint("to_employee_id IS NOT NULL OR to_department_id IS NOT NULL", name="ck_transfer_requests_target"),
        sa.ForeignKeyConstraint(["approver_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["from_department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["from_employee_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["requested_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["to_department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["to_employee_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transfer_requests_code"), "transfer_requests", ["code"], unique=True)
    op.create_index(op.f("ix_transfer_requests_asset_id"), "transfer_requests", ["asset_id"])
    op.create_index(op.f("ix_transfer_requests_status"), "transfer_requests", ["status"])
    op.create_index("uq_transfer_requests_one_requested_per_asset", "transfer_requests", ["asset_id"], unique=True, postgresql_where=sa.text("status = 'requested'"))

    op.create_table(
        "bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("asset_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("booked_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("purpose", sa.String(255), nullable=False),
        sa.Column("attendees", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.CheckConstraint("end_at > start_at", name="ck_bookings_time_order"),
        sa.CheckConstraint("status IN ('upcoming','ongoing','completed','cancelled')", name="ck_bookings_status"),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["booked_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bookings_asset_id"), "bookings", ["asset_id"])
    op.create_index(op.f("ix_bookings_booked_by_id"), "bookings", ["booked_by_id"])
    op.create_index(op.f("ix_bookings_start_at"), "bookings", ["start_at"])
    op.create_index(op.f("ix_bookings_end_at"), "bookings", ["end_at"])
    op.create_index(op.f("ix_bookings_status"), "bookings", ["status"])
    op.create_index("ix_bookings_overlap_lookup", "bookings", ["asset_id", "status", "start_at", "end_at"])

    op.create_table(
        "activity_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("module", sa.String(80), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("role", sa.String(32), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("status", sa.String(32), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_activity_logs_user_id"), "activity_logs", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_activity_logs_user_id"), table_name="activity_logs")
    op.drop_table("activity_logs")
    op.drop_index("ix_bookings_overlap_lookup", table_name="bookings")
    op.drop_index(op.f("ix_bookings_status"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_end_at"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_start_at"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_booked_by_id"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_asset_id"), table_name="bookings")
    op.drop_table("bookings")
    op.drop_index("uq_transfer_requests_one_requested_per_asset", table_name="transfer_requests")
    op.drop_index(op.f("ix_transfer_requests_status"), table_name="transfer_requests")
    op.drop_index(op.f("ix_transfer_requests_asset_id"), table_name="transfer_requests")
    op.drop_index(op.f("ix_transfer_requests_code"), table_name="transfer_requests")
    op.drop_table("transfer_requests")
    op.drop_index("uq_allocations_one_active_per_asset", table_name="allocations")
    op.drop_index(op.f("ix_allocations_status"), table_name="allocations")
    op.drop_index(op.f("ix_allocations_department_id"), table_name="allocations")
    op.drop_index(op.f("ix_allocations_employee_id"), table_name="allocations")
    op.drop_index(op.f("ix_allocations_asset_id"), table_name="allocations")
    op.drop_table("allocations")
