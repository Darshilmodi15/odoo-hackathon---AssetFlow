import os
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import Session, engine
from app.models.asset import Asset
from app.models.audit import AuditAssignment, AuditCycle, AuditFinding
from app.models.maintenance import MaintenanceHistory, MaintenanceRequest
from app.models.notification import Notification
from app.models.organization import AssetCategory, Department
from app.models.user import User
from app.models.workflow import ActivityLog, Allocation, Booking

DEMO_PASSWORD_ENV = "DEMO_PASSWORD"


def get_or_create_user(db: Session, *, name: str, email: str, role: str, department_id=None, password: str | None) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        user.role = role
        user.status = "active"
        if password:
            user.hashed_password = hash_password(password)
        if department_id:
            user.department_id = department_id
        return user
    if not password:
        raise RuntimeError(f"{DEMO_PASSWORD_ENV} is required to create missing demo user {email}")
    user = User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
        role=role,
        department_id=department_id,
        status="active",
    )
    db.add(user)
    db.flush()
    return user


def ensure_log(db: Session, *, user_id, action: str, module: str, entity_id, description: str, role: str, status: str | None = None) -> None:
    existing = db.scalar(select(ActivityLog).where(ActivityLog.action == action, ActivityLog.entity_id == entity_id))
    if existing:
        return
    db.add(ActivityLog(user_id=user_id, action=action, module=module, entity_id=entity_id, description=description, role=role, status=status))


def ensure_notification(db: Session, *, user_id, notification_type: str, title: str, message: str, link: str | None = None) -> None:
    existing = db.scalar(select(Notification).where(Notification.user_id == user_id, Notification.title == title, Notification.link == link))
    if existing:
        return
    db.add(Notification(user_id=user_id, type=notification_type, title=title, message=message, link=link, read=False))


def ensure_history(db: Session, *, request_id, status: str, by_id, note: str | None = None) -> None:
    existing = db.scalar(select(MaintenanceHistory).where(MaintenanceHistory.request_id == request_id, MaintenanceHistory.status == status))
    if existing:
        return
    db.add(MaintenanceHistory(request_id=request_id, status=status, by_id=by_id, note=note))


def main() -> int:
    password = os.getenv(DEMO_PASSWORD_ENV)
    with Session(engine) as db:
        eng = db.scalar(select(Department).where(Department.code == "DEMO-ENG"))
        if not eng:
            eng = Department(name="Demo Engineering", code="DEMO-ENG", status="active")
            db.add(eng)
            db.flush()
        ops = db.scalar(select(Department).where(Department.code == "DEMO-OPS"))
        if not ops:
            ops = Department(name="Demo Operations", code="DEMO-OPS", status="active")
            db.add(ops)
            db.flush()

        electronics = db.scalar(select(AssetCategory).where(AssetCategory.name == "Demo Electronics"))
        if not electronics:
            electronics = AssetCategory(name="Demo Electronics", description="Laptops and devices", status="active")
            db.add(electronics)
            db.flush()
        rooms = db.scalar(select(AssetCategory).where(AssetCategory.name == "Demo Rooms"))
        if not rooms:
            rooms = AssetCategory(name="Demo Rooms", description="Bookable meeting rooms", status="active")
            db.add(rooms)
            db.flush()
        furniture = db.scalar(select(AssetCategory).where(AssetCategory.name == "Demo Furniture"))
        if not furniture:
            furniture = AssetCategory(name="Demo Furniture", description="Desks and ergonomic equipment", status="active")
            db.add(furniture)
            db.flush()

        try:
            admin = get_or_create_user(db, name="Demo Admin", email="demo.admin@assetflow.local", role="admin", department_id=ops.id, password=password)
            manager = get_or_create_user(db, name="Demo Asset Manager", email="demo.manager@assetflow.local", role="asset_manager", department_id=ops.id, password=password)
            priya = get_or_create_user(db, name="Priya Shah", email="priya.demo@assetflow.local", role="employee", department_id=eng.id, password=password)
            arjun = get_or_create_user(db, name="Arjun Nair", email="arjun.demo@assetflow.local", role="employee", department_id=eng.id, password=password)
        except RuntimeError as exc:
            print(f"Demo seed skipped: {exc}")
            return 1

        assets = [
            ("AF-DEMO-001", "Demo MacBook Pro", electronics.id, "DEMO-SN-001", eng.id, "HQ Floor 3", "excellent", False, Decimal("180000")),
            ("AF-DEMO-002", "Demo ThinkPad", electronics.id, "DEMO-SN-002", eng.id, "HQ Floor 3", "good", False, Decimal("95000")),
            ("AF-DEMO-ROOM", "Demo Meeting Room B2", rooms.id, "DEMO-ROOM-B2", ops.id, "HQ Floor 2", "excellent", True, Decimal("0")),
        ]
        created_assets = []
        for tag, name, cat_id, serial, dept_id, location, condition, shared, cost in assets:
            asset = db.scalar(select(Asset).where(Asset.tag == tag))
            if not asset:
                asset = Asset(
                    tag=tag,
                    name=name,
                    category_id=cat_id,
                    serial_number=serial,
                    department_id=dept_id,
                    location=location,
                    condition=condition,
                    status="available",
                    shared=shared,
                    acquisition_date=date.today(),
                    acquisition_cost=cost,
                    notes="Demo seed asset",
                )
                db.add(asset)
                db.flush()
            created_assets.append(asset)

        laptop = created_assets[0]
        if not db.scalar(select(Allocation).where(Allocation.asset_id == laptop.id, Allocation.status == "active")):
            allocation = Allocation(
                asset_id=laptop.id,
                employee_id=priya.id,
                department_id=eng.id,
                allocated_at=datetime.now(timezone.utc),
                expected_return_at=datetime.now(timezone.utc) + timedelta(days=14),
                status="active",
                notes="Demo active allocation",
            )
            laptop.status = "allocated"
            laptop.assigned_to_id = priya.id
            db.add(allocation)

        room = created_assets[2]
        start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(minute=0, second=0, microsecond=0)
        if not db.scalar(select(Booking).where(Booking.asset_id == room.id, Booking.start_at == start)):
            booking = Booking(asset_id=room.id, booked_by_id=arjun.id, department_id=eng.id, start_at=start, end_at=start + timedelta(hours=1), purpose="Demo sprint planning", status="upcoming")
            db.add(booking)
            db.flush()
        else:
            booking = db.scalar(select(Booking).where(Booking.asset_id == room.id, Booking.start_at == start))

        pending = db.scalar(select(MaintenanceRequest).where(MaintenanceRequest.code == "MR-DEMO-001"))
        if not pending:
            pending = MaintenanceRequest(
                code="MR-DEMO-001",
                asset_id=created_assets[1].id,
                requested_by_id=priya.id,
                title="Keyboard intermittently unresponsive",
                description="Several keys on the demo ThinkPad need service before handoff.",
                priority="medium",
                status="pending",
                preferred_date=date.today() + timedelta(days=2),
            )
            db.add(pending)
            db.flush()
        ensure_history(db, request_id=pending.id, status="pending", by_id=priya.id, note="Ticket raised")
        ensure_log(db, user_id=priya.id, action="create_maintenance", module="Maintenance", entity_id=pending.id, description=f"Raised maintenance request {pending.code}", role=priya.role, status="success")

        resolved = db.scalar(select(MaintenanceRequest).where(MaintenanceRequest.code == "MR-DEMO-002"))
        if not resolved:
            resolved = MaintenanceRequest(
                code="MR-DEMO-002",
                asset_id=room.id,
                requested_by_id=arjun.id,
                title="Projector calibration completed",
                description="Meeting room display needed calibration for demo recording.",
                priority="low",
                status="resolved",
                preferred_date=date.today() - timedelta(days=1),
                technician_id=manager.id,
                estimated_cost=0,
                actual_cost=0,
                resolution_notes="Projector tested and room is ready.",
            )
            db.add(resolved)
            db.flush()
        for status_value, by_id, note in [
            ("pending", arjun.id, "Ticket raised"),
            ("approved", manager.id, "Approved for maintenance"),
            ("assigned", manager.id, "Assigned to demo asset manager"),
            ("in_progress", manager.id, "Work started"),
            ("resolved", manager.id, "Resolved and verified"),
        ]:
            ensure_history(db, request_id=resolved.id, status=status_value, by_id=by_id, note=note)
        ensure_log(db, user_id=manager.id, action="resolved_maintenance", module="Maintenance", entity_id=resolved.id, description=f"Resolved maintenance request {resolved.code}", role=manager.role, status="resolved")

        audit = db.scalar(select(AuditCycle).where(AuditCycle.title == "Demo Quarterly Asset Audit"))
        if not audit:
            audit = AuditCycle(
                title="Demo Quarterly Asset Audit",
                scope_department_id=eng.id,
                scope_location="HQ",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=7),
                status="active",
                notes="Seeded for final demo",
            )
            db.add(audit)
            db.flush()
        if not db.scalar(select(AuditAssignment).where(AuditAssignment.audit_cycle_id == audit.id, AuditAssignment.auditor_id == manager.id)):
            db.add(AuditAssignment(audit_cycle_id=audit.id, auditor_id=manager.id))
        finding_statuses = [("verified", "Asset verified in handoff area"), ("pending", None), ("damaged", "Projector remote casing cracked")]
        for asset, (finding_status, note) in zip(created_assets, finding_statuses):
            finding = db.scalar(select(AuditFinding).where(AuditFinding.audit_cycle_id == audit.id, AuditFinding.asset_id == asset.id))
            if not finding:
                finding = AuditFinding(audit_cycle_id=audit.id, asset_id=asset.id, status=finding_status, notes=note, auditor_id=manager.id if finding_status != "pending" else None)
                if finding_status != "pending":
                    finding.verified_at = datetime.now(timezone.utc)
                db.add(finding)
        ensure_log(db, user_id=admin.id, action="create_audit", module="Audits", entity_id=audit.id, description=f"Created audit cycle {audit.title}", role=admin.role, status="active")

        ensure_notification(db, user_id=priya.id, notification_type="allocation", title="Demo asset allocated", message="Demo MacBook Pro is allocated to you.", link="/allocations")
        ensure_notification(db, user_id=arjun.id, notification_type="booking", title="Demo booking confirmed", message="Demo Meeting Room B2 booking is confirmed.", link="/bookings")
        ensure_notification(db, user_id=priya.id, notification_type="maintenance", title="Demo maintenance request pending", message=f"{pending.code} is pending manager approval.", link=f"/maintenance/{pending.id}")
        ensure_notification(db, user_id=manager.id, notification_type="transfer", title="Demo transfer ready for review", message="A seeded transfer notification is available for the demo.", link="/allocations")
        ensure_notification(db, user_id=manager.id, notification_type="audit", title="Demo audit discrepancy flagged", message="One seeded audit finding is marked damaged.", link="/audits")

        db.commit()
        print("Demo seed complete: core workflow plus maintenance, audit, notifications and activity rows are ready.")
        print("Demo users: demo.admin@assetflow.local, demo.manager@assetflow.local, priya.demo@assetflow.local, arjun.demo@assetflow.local")
        return 0


if __name__ == "__main__":
    sys.exit(main())
