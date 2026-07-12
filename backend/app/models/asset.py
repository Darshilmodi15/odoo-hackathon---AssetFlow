import uuid
from datetime import date, datetime
from sqlalchemy import ForeignKey, String, Text, Boolean, Date, DateTime, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, GUID

class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    tag: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("asset_categories.id"), nullable=False
    )
    serial_number: Mapped[str] = mapped_column(
        String(120), unique=True, index=True, nullable=False
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("departments.id"), nullable=True
    )
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=True
    )
    location: Mapped[str] = mapped_column(String(120), nullable=False)
    condition: Mapped[str] = mapped_column(String(20), nullable=False)  # "excellent", "good", "fair", "poor"
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="available")  # e.g. "available", "allocated"
    shared: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    acquisition_date: Mapped[date] = mapped_column(Date, nullable=False)
    acquisition_cost: Mapped[float] = mapped_column(Numeric, default=0.0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    category = relationship("AssetCategory", foreign_keys=[category_id])
    department = relationship("Department", foreign_keys=[department_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])


class Allocation(Base):
    __tablename__ = "allocations"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("assets.id"), nullable=False
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("departments.id"), nullable=True
    )
    allocated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expected_return_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    returned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    return_condition: Mapped[str | None] = mapped_column(String(20), nullable=True)
    return_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")  # "active", "returned", "overdue"
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    asset = relationship("Asset", foreign_keys=[asset_id])
    employee = relationship("User", foreign_keys=[employee_id])
    department = relationship("Department", foreign_keys=[department_id])


class TransferRequest(Base):
    __tablename__ = "transfer_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("assets.id"), nullable=False
    )
    from_employee_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    to_employee_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    approver_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="requested")  # "requested", "approved", "rejected", "completed"

    asset = relationship("Asset", foreign_keys=[asset_id])
    from_employee = relationship("User", foreign_keys=[from_employee_id])
    to_employee = relationship("User", foreign_keys=[to_employee_id])
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    approver = relationship("User", foreign_keys=[approver_id])


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("assets.id"), nullable=False
    )
    booked_by_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("departments.id"), nullable=True
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    attendees: Mapped[int | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="upcoming")  # "upcoming", "ongoing", "completed", "cancelled"

    asset = relationship("Asset", foreign_keys=[asset_id])
    booked_by = relationship("User", foreign_keys=[booked_by_id])
    department = relationship("Department", foreign_keys=[department_id])
