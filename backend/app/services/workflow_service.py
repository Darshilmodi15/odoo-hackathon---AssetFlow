import uuid
from datetime import datetime, timezone

from fastapi import status
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.core.errors import api_error
from app.models.asset import Asset
from app.models.organization import Department
from app.models.user import User
from app.models.workflow import Allocation, Booking, TransferRequest
from app.schemas.workflow import AllocationCreate, AllocationReturn, BookingCreate, BookingUpdate, TransferCreate

ALLOCATABLE_ASSET_STATUS = "available"
BLOCKING_BOOKING_STATUSES = {"upcoming", "ongoing"}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _active_allocation_stmt(asset_id: uuid.UUID):
    return select(Allocation).where(Allocation.asset_id == asset_id, Allocation.status == "active")


def list_allocations(db: Session, current_user: User, **filters) -> list[Allocation]:
    stmt = select(Allocation).order_by(Allocation.allocated_at.desc())
    if current_user.role == "employee":
        stmt = stmt.where(Allocation.employee_id == current_user.id)
    elif current_user.role == "department_head" and current_user.department_id:
        stmt = stmt.where(Allocation.department_id == current_user.department_id)
    for field in ["employee_id", "asset_id", "department_id", "status"]:
        if filters.get(field) is not None:
            stmt = stmt.where(getattr(Allocation, field) == filters[field])
    if filters.get("overdue"):
        stmt = stmt.where(Allocation.status == "active", Allocation.expected_return_at < utcnow())
    return list(db.scalars(stmt).all())


def get_allocation(db: Session, allocation_id: uuid.UUID, current_user: User) -> Allocation:
    allocation = db.get(Allocation, allocation_id)
    if not allocation:
        raise api_error(status.HTTP_404_NOT_FOUND, "Allocation not found", "ALLOCATION_NOT_FOUND")
    if current_user.role in {"admin", "asset_manager"} or allocation.employee_id == current_user.id:
        return allocation
    if current_user.role == "department_head" and allocation.department_id == current_user.department_id:
        return allocation
    raise api_error(status.HTTP_403_FORBIDDEN, "Not enough permissions", "FORBIDDEN_ROLE")


def create_allocation(db: Session, payload: AllocationCreate, actor: User) -> Allocation:
    if actor.role not in {"admin", "asset_manager", "department_head"}:
        raise api_error(status.HTTP_403_FORBIDDEN, "Employees cannot directly allocate assets", "FORBIDDEN_ROLE")
    asset = db.scalar(select(Asset).where(Asset.id == payload.asset_id).with_for_update())
    if not asset:
        raise api_error(status.HTTP_404_NOT_FOUND, "Asset not found", "ASSET_NOT_FOUND")
    if asset.status != ALLOCATABLE_ASSET_STATUS:
        raise api_error(status.HTTP_409_CONFLICT, "Asset is not available for allocation", "ASSET_ALREADY_ALLOCATED")
    if db.scalar(_active_allocation_stmt(asset.id).with_for_update()):
        raise api_error(status.HTTP_409_CONFLICT, "Asset already has an active allocation", "ASSET_ALREADY_ALLOCATED")
    employee = db.get(User, payload.employee_id) if payload.employee_id else None
    department = db.get(Department, payload.department_id) if payload.department_id else None
    if payload.employee_id and not employee:
        raise api_error(status.HTTP_404_NOT_FOUND, "User not found", "USER_NOT_FOUND")
    if payload.department_id and not department:
        raise api_error(status.HTTP_404_NOT_FOUND, "Department not found", "USER_NOT_FOUND")
    target_department_id = payload.department_id or (employee.department_id if employee else None)
    if actor.role == "department_head" and actor.department_id != target_department_id:
        raise api_error(status.HTTP_403_FORBIDDEN, "Department heads can allocate only inside their department", "FORBIDDEN_ROLE")
    allocation = Allocation(
        asset_id=asset.id,
        employee_id=payload.employee_id,
        department_id=target_department_id,
        allocated_at=_as_utc(payload.allocation_date) or utcnow(),
        expected_return_at=_as_utc(payload.expected_return_at or payload.expected_return_date),
        status="active",
        notes=payload.notes,
    )
    asset.status = "allocated"
    asset.assigned_to_id = payload.employee_id
    asset.department_id = target_department_id
    db.add(allocation)
    db.commit()
    db.refresh(allocation)
    return allocation


def return_allocation(db: Session, allocation_id: uuid.UUID, payload: AllocationReturn, actor: User) -> Allocation:
    if actor.role not in {"admin", "asset_manager", "department_head"}:
        raise api_error(status.HTTP_403_FORBIDDEN, "Not enough permissions", "FORBIDDEN_ROLE")
    allocation = db.scalar(select(Allocation).where(Allocation.id == allocation_id).with_for_update())
    if not allocation:
        raise api_error(status.HTTP_404_NOT_FOUND, "Allocation not found", "ALLOCATION_NOT_FOUND")
    if allocation.status != "active":
        raise api_error(status.HTTP_409_CONFLICT, "Allocation is already returned", "ALLOCATION_ALREADY_RETURNED")
    if actor.role == "department_head" and allocation.department_id != actor.department_id:
        raise api_error(status.HTTP_403_FORBIDDEN, "Not enough permissions", "FORBIDDEN_ROLE")
    asset = db.scalar(select(Asset).where(Asset.id == allocation.asset_id).with_for_update())
    allocation.status = "returned"
    allocation.returned_at = _as_utc(payload.return_date) or utcnow()
    allocation.return_condition = payload.condition_at_return
    allocation.return_notes = payload.condition_notes
    allocation.return_document_url = payload.document_url
    if asset:
        asset.condition = payload.condition_at_return
        asset.status = "available"
        asset.assigned_to_id = None
    db.commit()
    db.refresh(allocation)
    return allocation


def list_transfers(db: Session, current_user: User) -> list[TransferRequest]:
    stmt = select(TransferRequest).order_by(TransferRequest.requested_at.desc())
    if current_user.role == "employee":
        stmt = stmt.where((TransferRequest.requested_by_id == current_user.id) | (TransferRequest.to_employee_id == current_user.id) | (TransferRequest.from_employee_id == current_user.id))
    elif current_user.role == "department_head" and current_user.department_id:
        stmt = stmt.where((TransferRequest.to_department_id == current_user.department_id) | (TransferRequest.from_department_id == current_user.department_id))
    return list(db.scalars(stmt).all())


def get_transfer(db: Session, transfer_id: uuid.UUID, current_user: User) -> TransferRequest:
    transfer = db.get(TransferRequest, transfer_id)
    if not transfer:
        raise api_error(status.HTTP_404_NOT_FOUND, "Transfer not found", "TRANSFER_CONFLICT")
    return transfer


def _next_transfer_code(db: Session) -> str:
    count = db.scalar(select(func.count()).select_from(TransferRequest)) or 0
    return f"TR-{count + 1:04d}"


def create_transfer(db: Session, payload: TransferCreate, actor: User) -> TransferRequest:
    active = db.scalar(_active_allocation_stmt(payload.asset_id).with_for_update())
    if not active:
        raise api_error(status.HTTP_409_CONFLICT, "Asset does not have an active allocation", "TRANSFER_CONFLICT")
    if db.scalar(select(TransferRequest).where(TransferRequest.asset_id == payload.asset_id, TransferRequest.status == "requested").with_for_update()):
        raise api_error(status.HTTP_409_CONFLICT, "A pending transfer already exists for this asset", "TRANSFER_CONFLICT")
    to_user_id = payload.requested_to_user_id or payload.to_employee_id
    to_department_id = payload.requested_to_department_id or payload.to_department_id
    if to_user_id and not db.get(User, to_user_id):
        raise api_error(status.HTTP_404_NOT_FOUND, "User not found", "USER_NOT_FOUND")
    if to_department_id and not db.get(Department, to_department_id):
        raise api_error(status.HTTP_404_NOT_FOUND, "Department not found", "USER_NOT_FOUND")
    transfer = TransferRequest(
        code=_next_transfer_code(db),
        asset_id=payload.asset_id,
        from_employee_id=active.employee_id,
        from_department_id=active.department_id,
        to_employee_id=to_user_id,
        to_department_id=to_department_id,
        reason=payload.reason,
        requested_by_id=actor.id,
        status="requested",
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    return transfer


def update_transfer_status(db: Session, transfer_id: uuid.UUID, new_status: str, actor: User) -> TransferRequest:
    if actor.role not in {"admin", "asset_manager", "department_head"}:
        raise api_error(status.HTTP_403_FORBIDDEN, "Not enough permissions", "FORBIDDEN_ROLE")
    transfer = db.scalar(select(TransferRequest).where(TransferRequest.id == transfer_id).with_for_update())
    if not transfer or transfer.status != "requested":
        raise api_error(status.HTTP_409_CONFLICT, "Transfer cannot be updated", "TRANSFER_CONFLICT")
    active = db.scalar(_active_allocation_stmt(transfer.asset_id).with_for_update())
    if not active:
        raise api_error(status.HTTP_409_CONFLICT, "Asset does not have an active allocation", "TRANSFER_CONFLICT")
    transfer.approver_id = actor.id
    transfer.decided_at = utcnow()
    if new_status == "rejected":
        transfer.status = "rejected"
    elif new_status == "approved":
        active.status = "transferred"
        active.returned_at = utcnow()
        new_allocation = Allocation(asset_id=transfer.asset_id, employee_id=transfer.to_employee_id, department_id=transfer.to_department_id, allocated_at=utcnow(), status="active", notes=f"Created from transfer {transfer.code}")
        asset = db.scalar(select(Asset).where(Asset.id == transfer.asset_id).with_for_update())
        if asset:
            asset.status = "allocated"
            asset.assigned_to_id = transfer.to_employee_id
            asset.department_id = transfer.to_department_id
        db.add(new_allocation)
        transfer.status = "completed"
    db.commit()
    db.refresh(transfer)
    return transfer


def list_bookings(db: Session, current_user: User) -> list[Booking]:
    stmt = select(Booking).order_by(Booking.start_at.desc())
    if current_user.role == "employee":
        stmt = stmt.where(Booking.booked_by_id == current_user.id)
    elif current_user.role == "department_head" and current_user.department_id:
        stmt = stmt.where(Booking.department_id == current_user.department_id)
    return list(db.scalars(stmt).all())


def get_booking(db: Session, booking_id: uuid.UUID, current_user: User) -> Booking:
    booking = db.get(Booking, booking_id)
    if not booking:
        raise api_error(status.HTTP_404_NOT_FOUND, "Booking not found", "BOOKING_NOT_FOUND")
    if current_user.role in {"admin", "asset_manager"} or booking.booked_by_id == current_user.id:
        return booking
    if current_user.role == "department_head" and booking.department_id == current_user.department_id:
        return booking
    raise api_error(status.HTTP_403_FORBIDDEN, "Not enough permissions", "FORBIDDEN_ROLE")


def _find_booking_conflict(db: Session, asset_id: uuid.UUID, start_at: datetime, end_at: datetime, exclude_id: uuid.UUID | None = None) -> Booking | None:
    stmt = select(Booking).where(Booking.asset_id == asset_id, Booking.status.in_(BLOCKING_BOOKING_STATUSES), start_at < Booking.end_at, end_at > Booking.start_at).with_for_update()
    if exclude_id:
        stmt = stmt.where(Booking.id != exclude_id)
    return db.scalar(stmt)


def suggest_next_slot(db: Session, asset_id: uuid.UUID, start_at: datetime, end_at: datetime) -> dict:
    duration = end_at - start_at
    latest = db.scalar(select(func.max(Booking.end_at)).where(Booking.asset_id == asset_id, Booking.status.in_(BLOCKING_BOOKING_STATUSES)))
    next_start = max(latest or end_at, end_at)
    return {"asset_id": str(asset_id), "start_at": next_start.isoformat(), "end_at": (next_start + duration).isoformat(), "reason": "Same resource, later time"}


def _booking_values(payload: BookingCreate) -> tuple[uuid.UUID, datetime, datetime]:
    return payload.asset_id or payload.resource_id, _as_utc(payload.start_at or payload.start_time), _as_utc(payload.end_at or payload.end_time)  # type: ignore[return-value]


def create_booking(db: Session, payload: BookingCreate, actor: User) -> Booking:
    asset_id, start_at, end_at = _booking_values(payload)
    asset = db.scalar(select(Asset).where(Asset.id == asset_id).with_for_update())
    if not asset:
        raise api_error(status.HTTP_404_NOT_FOUND, "Asset not found", "ASSET_NOT_FOUND")
    if not asset.shared:
        raise api_error(status.HTTP_409_CONFLICT, "Resource is not bookable", "BOOKING_TIME_CONFLICT")
    conflict = _find_booking_conflict(db, asset_id, start_at, end_at)
    if conflict:
        exc = api_error(status.HTTP_409_CONFLICT, "Resource is already booked during this time", "BOOKING_TIME_CONFLICT")
        exc.detail = {"detail": "Resource is already booked during this time", "code": "BOOKING_TIME_CONFLICT", "conflicting_booking": {"start_time": conflict.start_at.isoformat(), "end_time": conflict.end_at.isoformat()}, "suggestions": [suggest_next_slot(db, asset_id, start_at, end_at)]}
        raise exc
    booking = Booking(asset_id=asset_id, booked_by_id=actor.id, department_id=payload.department_id or actor.department_id, start_at=start_at, end_at=end_at, purpose=payload.purpose, attendees=payload.attendees, notes=payload.notes, status="upcoming")
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def update_booking(db: Session, booking_id: uuid.UUID, payload: BookingUpdate, actor: User) -> Booking:
    booking = get_booking(db, booking_id, actor)
    if actor.role == "employee" and booking.booked_by_id != actor.id:
        raise api_error(status.HTTP_403_FORBIDDEN, "Not enough permissions", "FORBIDDEN_ROLE")
    start_at = _as_utc(payload.start_at or payload.start_time) or booking.start_at
    end_at = _as_utc(payload.end_at or payload.end_time) or booking.end_at
    if end_at <= start_at:
        raise api_error(status.HTTP_422_UNPROCESSABLE_ENTITY, "end_time must be later than start_time", "BOOKING_TIME_CONFLICT")
    if (start_at != booking.start_at or end_at != booking.end_at) and payload.status != "cancelled":
        conflict = _find_booking_conflict(db, booking.asset_id, start_at, end_at, booking.id)
        if conflict:
            raise api_error(status.HTTP_409_CONFLICT, "Resource is already booked during this time", "BOOKING_TIME_CONFLICT")
    booking.start_at = start_at
    booking.end_at = end_at
    if payload.purpose is not None:
        booking.purpose = payload.purpose
    if payload.department_id is not None:
        booking.department_id = payload.department_id
    if payload.attendees is not None:
        booking.attendees = payload.attendees
    if payload.notes is not None:
        booking.notes = payload.notes
    if payload.status is not None:
        booking.status = payload.status
    db.commit()
    db.refresh(booking)
    return booking


def cancel_booking(db: Session, booking_id: uuid.UUID, actor: User) -> Booking:
    booking = get_booking(db, booking_id, actor)
    if actor.role == "employee" and booking.booked_by_id != actor.id:
        raise api_error(status.HTTP_403_FORBIDDEN, "Not enough permissions", "FORBIDDEN_ROLE")
    booking.status = "cancelled"
    db.commit()
    db.refresh(booking)
    return booking
