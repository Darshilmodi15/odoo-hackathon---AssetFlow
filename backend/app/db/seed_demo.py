import os
import sys
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import Session, engine
from app.models.asset import Asset
from app.models.organization import AssetCategory, Department
from app.models.user import User
from app.models.workflow import Allocation, Booking

DEMO_PASSWORD_ENV = "DEMO_PASSWORD"


def get_or_create_user(db: Session, *, name: str, email: str, role: str, department_id=None, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        user.role = role
        user.status = "active"
        if department_id:
            user.department_id = department_id
        return user
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


def main() -> int:
    password = os.getenv(DEMO_PASSWORD_ENV)
    if not password:
        print(f"Demo seed skipped: {DEMO_PASSWORD_ENV} is required.")
        return 1
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

        admin = get_or_create_user(db, name="Demo Admin", email="demo.admin@assetflow.local", role="admin", department_id=ops.id, password=password)
        manager = get_or_create_user(db, name="Demo Asset Manager", email="demo.manager@assetflow.local", role="asset_manager", department_id=ops.id, password=password)
        priya = get_or_create_user(db, name="Priya Shah", email="priya.demo@assetflow.local", role="employee", department_id=eng.id, password=password)
        arjun = get_or_create_user(db, name="Arjun Nair", email="arjun.demo@assetflow.local", role="employee", department_id=eng.id, password=password)

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
            db.add(Booking(asset_id=room.id, booked_by_id=arjun.id, department_id=eng.id, start_at=start, end_at=start + timedelta(hours=1), purpose="Demo sprint planning", status="upcoming"))

        db.commit()
        print("Demo seed complete: users, departments, categories, assets, allocation and booking are ready.")
        print("Demo users: demo.admin@assetflow.local, demo.manager@assetflow.local, priya.demo@assetflow.local, arjun.demo@assetflow.local")
        return 0


if __name__ == "__main__":
    sys.exit(main())
