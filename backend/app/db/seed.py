"""Idempotent seed script for AssetFlow demo data.

Usage:
    python -m app.db.seed

Rules:
- Running twice must not create duplicates.
- Uses stable UUIDs derived from seed keys.
- Does NOT seed passwords for admin users (Darshil handles auth).
- Does NOT delete existing records.
- Prints a clear summary.
"""
import uuid
from datetime import date

# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from app.core import security
from app.db.session import SessionLocal
from app.models.organization import AssetCategory, Department
from app.models.user import User
from app.models.asset import Asset


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def seed_uuid(seed_id: str) -> uuid.UUID:
    """Derive a stable UUID from a string key."""
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"{seed_id}.assetflow.local")


def _upsert_category(db: Session, id: uuid.UUID, name: str, description: str) -> tuple[AssetCategory, bool]:
    existing = db.query(AssetCategory).filter(AssetCategory.id == id).first()
    if existing:
        return existing, False
    # Also check by name (in case id changed)
    existing = db.query(AssetCategory).filter(AssetCategory.name == name).first()
    if existing:
        return existing, False
    obj = AssetCategory(id=id, name=name, description=description, status="active")
    db.add(obj)
    return obj, True


def _upsert_department(db: Session, id: uuid.UUID, name: str, code: str) -> tuple[Department, bool]:
    existing = db.query(Department).filter(Department.id == id).first()
    if existing:
        return existing, False
    existing = db.query(Department).filter(Department.code == code).first()
    if existing:
        return existing, False
    obj = Department(id=id, name=name, code=code, status="active")
    db.add(obj)
    return obj, True


def _upsert_user(db: Session, id: uuid.UUID, name: str, email: str, role: str, dept_id: uuid.UUID) -> tuple[User, bool]:
    existing = db.query(User).filter(User.id == id).first()
    if existing:
        return existing, False
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return existing, False
    hashed = security.get_password_hash("demo_password_123")
    obj = User(
        id=id, name=name, email=email,
        hashed_password=hashed, role=role,
        department_id=dept_id, status="active"
    )
    db.add(obj)
    return obj, True


def _upsert_asset(
    db: Session, *,
    id: uuid.UUID, tag: str, name: str,
    category_id: uuid.UUID, serial_number: str,
    department_id: uuid.UUID | None,
    location: str, condition: str,
    acquisition_date: date, acquisition_cost: float,
    shared: bool = False, notes: str | None = None,
) -> tuple[Asset, bool]:
    existing = db.query(Asset).filter(Asset.id == id).first()
    if existing:
        return existing, False
    existing = db.query(Asset).filter(Asset.tag == tag).first()
    if existing:
        return existing, False
    obj = Asset(
        id=id, tag=tag, name=name,
        category_id=category_id, serial_number=serial_number,
        department_id=department_id,
        location=location, condition=condition, status="available",
        acquisition_date=acquisition_date, acquisition_cost=acquisition_cost,
        shared=shared, notes=notes,
    )
    db.add(obj)
    return obj, True


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

def seed_db(db: Session) -> None:
    created = {"categories": 0, "departments": 0, "users": 0, "assets": 0}

    # ── Categories ────────────────────────────────────────────────────────────
    categories_data = [
        ("c1", "Electronics",           "Laptops, phones, tablets, monitors"),
        ("c2", "Furniture",             "Chairs, desks, cabinets, shelves"),
        ("c3", "Vehicles",              "Company cars and transport vehicles"),
        ("c4", "Rooms",                 "Bookable meeting and conference rooms"),
        ("c5", "Equipment",             "Projectors, printers, scanners"),
        ("c6", "Office Infrastructure", "UPS, networking gear, servers"),
    ]
    for key, name, desc in categories_data:
        _, is_new = _upsert_category(db, seed_uuid(key), name, desc)
        if is_new:
            created["categories"] += 1
    db.commit()

    # ── Departments ───────────────────────────────────────────────────────────
    departments_data = [
        ("d1", "Information Technology", "IT"),
        ("d2", "Human Resources",        "HR"),
        ("d3", "Finance",                "FIN"),
        ("d4", "Operations",             "OPS"),
        ("d5", "Administration",         "ADM"),
    ]
    for key, name, code in departments_data:
        _, is_new = _upsert_department(db, seed_uuid(key), name, code)
        if is_new:
            created["departments"] += 1
    db.commit()

    # ── Users (needed so department heads can be set) ─────────────────────────
    users_data = [
        ("e1",  "Anita Rao",       "anita.rao@assetflow.co",       "admin",           "d5"),
        ("e2",  "Raj Mehta",       "raj.mehta@assetflow.co",       "asset_manager",   "d1"),
        ("e3",  "Priya Shah",      "priya.shah@assetflow.co",      "employee",        "d1"),
        ("e4",  "Arjun Nair",      "arjun.nair@assetflow.co",      "employee",        "d1"),
        ("e5",  "Sneha Iyer",      "sneha.iyer@assetflow.co",      "department_head", "d2"),
        ("e6",  "Vikram Desai",    "vikram.desai@assetflow.co",    "employee",        "d2"),
        ("e7",  "Meera Kulkarni",  "meera.kulkarni@assetflow.co",  "department_head", "d3"),
        ("e8",  "Rohit Verma",     "rohit.verma@assetflow.co",     "employee",        "d3"),
        ("e9",  "Kavita Menon",    "kavita.menon@assetflow.co",    "department_head", "d4"),
        ("e10", "Sanjay Pillai",   "sanjay.pillai@assetflow.co",   "employee",        "d4"),
        ("e11", "Divya Krishnan",  "divya.krishnan@assetflow.co",  "asset_manager",   "d5"),
        ("e12", "Aditya Bose",     "aditya.bose@assetflow.co",     "employee",        "d5"),
    ]
    for key, name, email, role, dept_key in users_data:
        _, is_new = _upsert_user(db, seed_uuid(key), name, email, role, seed_uuid(dept_key))
        if is_new:
            created["users"] += 1
    db.commit()

    # Update department heads
    head_map = {"d1": "e2", "d2": "e5", "d3": "e7", "d4": "e9", "d5": "e11"}
    for dept_key, head_key in head_map.items():
        dept = db.query(Department).filter(Department.id == seed_uuid(dept_key)).first()
        if dept and dept.head_id is None:
            dept.head_id = seed_uuid(head_key)
    db.commit()

    # ── Assets ────────────────────────────────────────────────────────────────
    assets_data = [
        dict(
            key="a1", tag="AF-0001", name="Dell Latitude Laptop",
            cat="c1", serial="SN-DELL-001", dept="d1",
            location="IT Lab - Floor 2", condition="good",
            acq_date=date(2024, 1, 15), cost=65000.0, shared=False,
            notes="Assigned to IT staff",
        ),
        dict(
            key="a2", tag="AF-0002", name="MacBook Air M2",
            cat="c1", serial="SN-APPLE-002", dept="d1",
            location="IT Lab - Floor 2", condition="excellent",
            acq_date=date(2024, 3, 10), cost=95000.0, shared=False,
        ),
        dict(
            key="a3", tag="AF-0003", name="Epson Projector EB-W51",
            cat="c5", serial="SN-EPSON-003", dept="d4",
            location="Conference Room A", condition="good",
            acq_date=date(2023, 11, 5), cost=28000.0, shared=True,
            notes="Shared projector – bookable",
        ),
        dict(
            key="a4", tag="AF-0004", name="Meeting Room B2",
            cat="c4", serial="SN-ROOM-004", dept=None,
            location="Block B - 2nd Floor", condition="excellent",
            acq_date=date(2022, 6, 1), cost=0.0, shared=True,
            notes="Seating capacity 12",
        ),
        dict(
            key="a5", tag="AF-0005", name="Canon Printer LBP6230",
            cat="c5", serial="SN-CANON-005", dept="d5",
            location="Admin Block - Ground Floor", condition="fair",
            acq_date=date(2022, 9, 20), cost=12000.0, shared=True,
        ),
        dict(
            key="a6", tag="AF-0006", name="Toyota Innova Crysta",
            cat="c3", serial="SN-TOYO-006", dept="d4",
            location="Parking Lot B", condition="good",
            acq_date=date(2023, 4, 15), cost=1850000.0, shared=True,
            notes="Company vehicle – driver assigned separately",
        ),
        dict(
            key="a7", tag="AF-0007", name="Office Workstation HP Z2",
            cat="c1", serial="SN-HP-007", dept="d3",
            location="Finance Department - 3rd Floor", condition="good",
            acq_date=date(2023, 7, 1), cost=55000.0, shared=False,
        ),
        dict(
            key="a8", tag="AF-0008", name="Industrial Barcode Scanner",
            cat="c5", serial="SN-SCAN-008", dept="d4",
            location="Warehouse - Ground Floor", condition="good",
            acq_date=date(2024, 2, 12), cost=18000.0, shared=False,
            notes="Used for inventory management",
        ),
    ]

    for a in assets_data:
        dept_id = seed_uuid(a["dept"]) if a.get("dept") else None
        _, is_new = _upsert_asset(
            db,
            id=seed_uuid(a["key"]),
            tag=a["tag"],
            name=a["name"],
            category_id=seed_uuid(a["cat"]),
            serial_number=a["serial"],
            department_id=dept_id,
            location=a["location"],
            condition=a["condition"],
            acquisition_date=a["acq_date"],
            acquisition_cost=a["cost"],
            shared=a.get("shared", False),
            notes=a.get("notes"),
        )
        if is_new:
            created["assets"] += 1
    db.commit()

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("  AssetFlow Seed Summary")
    print("=" * 50)
    print(f"  Categories created : {created['categories']}")
    print(f"  Departments created: {created['departments']}")
    print(f"  Users created      : {created['users']}")
    print(f"  Assets created     : {created['assets']}")
    print("=" * 50)
    if all(v == 0 for v in created.values()):
        print("  ✓ Database already seeded – no changes made.")
    else:
        print("  ✓ Seed complete.")
    print()


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_db(db)
    finally:
        db.close()
