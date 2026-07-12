import uuid
from datetime import date, datetime
from sqlalchemy import ForeignKey, String, Text, Numeric, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, GUID

class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("assets.id"), nullable=False
    )
    requested_by_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)  # "low", "medium", "high", "critical"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # "pending", "approved", "rejected", "assigned", "in_progress", "resolved"
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    preferred_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    technician_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=True
    )
    estimated_cost: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    actual_cost: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    asset = relationship("Asset", foreign_keys=[asset_id])
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    technician = relationship("User", foreign_keys=[technician_id])


class MaintenanceHistory(Base):
    __tablename__ = "maintenance_history"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    request_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("maintenance_requests.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    by_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    request = relationship("MaintenanceRequest", foreign_keys=[request_id], backref="history_entries")
    by = relationship("User", foreign_keys=[by_id])
