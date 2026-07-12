import uuid
from datetime import date, datetime
from sqlalchemy import ForeignKey, String, Text, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, GUID

class AuditCycle(Base):
    __tablename__ = "audit_cycles"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    scope_department_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("departments.id"), nullable=True
    )
    scope_location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")  # "draft", "active", "in_review", "closed"
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    scope_department = relationship("Department", foreign_keys=[scope_department_id])


class AuditAssignment(Base):
    __tablename__ = "audit_assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    audit_cycle_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("audit_cycles.id"), nullable=False
    )
    auditor_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )

    audit_cycle = relationship("AuditCycle", foreign_keys=[audit_cycle_id], backref="assignments")
    auditor = relationship("User", foreign_keys=[auditor_id])


class AuditFinding(Base):
    __tablename__ = "audit_findings"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    audit_cycle_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("audit_cycles.id"), nullable=False
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("assets.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # "pending", "verified", "missing", "damaged"
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    auditor_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    audit_cycle = relationship("AuditCycle", foreign_keys=[audit_cycle_id], backref="findings")
    asset = relationship("Asset", foreign_keys=[asset_id])
    auditor = relationship("User", foreign_keys=[auditor_id])
