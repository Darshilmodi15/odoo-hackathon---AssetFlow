import os
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_session
from app.main import app
from app.models.asset import Asset
from app.models.organization import AssetCategory, Department
from app.models.user import User

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
ALLOW_RESET = os.getenv("ASSETFLOW_ALLOW_TEST_DB_RESET") == "true"
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL or not ALLOW_RESET,
    reason="Set TEST_DATABASE_URL and ASSETFLOW_ALLOW_TEST_DB_RESET=true to run DB workflow tests safely.",
)


@pytest.fixture()
def client():
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_session():
        with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def seeded(client):
    override = app.dependency_overrides[get_session]
    db: Session = next(override())
    dept = Department(name="Engineering", code="ENG", status="active")
    category = AssetCategory(name="Laptop", status="active")
    admin = User(name="Admin", email="admin@example.com", hashed_password=hash_password("password123"), role="admin", status="active")
    manager = User(name="Manager", email="manager@example.com", hashed_password=hash_password("password123"), role="asset_manager", status="active", department=dept)
    employee = User(name="Employee", email="employee@example.com", hashed_password=hash_password("password123"), role="employee", status="active", department=dept)
    employee2 = User(name="Employee Two", email="employee2@example.com", hashed_password=hash_password("password123"), role="employee", status="active", department=dept)
    db.add_all([dept, category, admin, manager, employee, employee2])
    db.flush()
    asset = Asset(tag="AF-0001", name="MacBook", category_id=category.id, serial_number="SN-1", department_id=dept.id, location="HQ", condition="excellent", status="available", shared=False, acquisition_date=date.today(), acquisition_cost=1000)
    room = Asset(tag="AF-0002", name="Meeting Room", category_id=category.id, serial_number="ROOM-1", department_id=dept.id, location="HQ", condition="excellent", status="available", shared=True, acquisition_date=date.today(), acquisition_cost=0)
    db.add_all([asset, room])
    db.commit()
    data = {"dept": dept.id, "asset": asset.id, "room": room.id, "admin": admin.id, "manager": manager.id, "employee": employee.id, "employee2": employee2.id}
    db.close()
    return data


def login(client, email):
    res = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_auth_and_role_promotion(client, seeded):
    res = client.post("/api/auth/signup", json={"name": "Priya", "email": "PRIYA@example.com", "password": "securepass123", "role": "admin"})
    assert res.status_code == 201
    assert res.json()["role"] == "employee"
    duplicate = client.post("/api/auth/signup", json={"name": "Priya", "email": "priya@example.com", "password": "securepass123"})
    assert duplicate.status_code == 409
    assert client.post("/api/auth/login", json={"email": "priya@example.com", "password": "wrongpass"}).status_code == 401
    assert client.get("/api/auth/me").status_code == 401
    employee_headers = login(client, "employee@example.com")
    assert client.patch(f"/api/users/{seeded['employee']}/role", json={"role": "asset_manager"}, headers=employee_headers).status_code == 403
    admin_headers = login(client, "admin@example.com")
    promoted = client.patch(f"/api/users/{seeded['employee']}/role", json={"role": "asset_manager"}, headers=admin_headers)
    assert promoted.status_code == 200
    assert promoted.json()["role"] == "asset_manager"


def test_allocation_return_transfer_and_booking(client, seeded):
    manager_headers = login(client, "manager@example.com")
    employee_headers = login(client, "employee@example.com")
    alloc = client.post("/api/allocations", json={"asset_id": str(seeded["asset"]), "employee_id": str(seeded["employee"]), "notes": "demo"}, headers=manager_headers)
    assert alloc.status_code == 201
    allocation_id = alloc.json()["id"]
    assert client.post("/api/allocations", json={"asset_id": str(seeded["asset"]), "employee_id": str(seeded["employee2"])}, headers=manager_headers).status_code == 409
    transfer = client.post("/api/transfers", json={"asset_id": str(seeded["asset"]), "to_employee_id": str(seeded["employee2"]), "reason": "handoff"}, headers=employee_headers)
    assert transfer.status_code == 201
    assert client.post("/api/transfers", json={"asset_id": str(seeded["asset"]), "to_employee_id": str(seeded["employee2"]), "reason": "again"}, headers=employee_headers).status_code == 409
    approved = client.patch(f"/api/transfers/{transfer.json()['id']}/status", json={"status": "approved"}, headers=manager_headers)
    assert approved.status_code == 200
    returned = client.post(f"/api/allocations/{allocation_id}/return", json={"condition_at_return": "good", "condition_notes": "ok"}, headers=manager_headers)
    assert returned.status_code == 409

    start = datetime(2026, 7, 15, 9, tzinfo=timezone.utc)
    end = start + timedelta(hours=1)
    booking = client.post("/api/bookings", json={"asset_id": str(seeded["room"]), "start_at": start.isoformat(), "end_at": end.isoformat(), "purpose": "Planning"}, headers=employee_headers)
    assert booking.status_code == 201
    overlap = client.post("/api/bookings", json={"asset_id": str(seeded["room"]), "start_at": (start + timedelta(minutes=30)).isoformat(), "end_at": (end + timedelta(minutes=30)).isoformat(), "purpose": "Overlap"}, headers=employee_headers)
    assert overlap.status_code == 409
    adjacent = client.post("/api/bookings", json={"asset_id": str(seeded["room"]), "start_at": end.isoformat(), "end_at": (end + timedelta(hours=1)).isoformat(), "purpose": "Adjacent"}, headers=employee_headers)
    assert adjacent.status_code == 201
    assert client.delete(f"/api/bookings/{booking.json()['id']}", headers=employee_headers).status_code == 200
    reused = client.post("/api/bookings", json={"asset_id": str(seeded["room"]), "start_at": start.isoformat(), "end_at": end.isoformat(), "purpose": "Reused"}, headers=employee_headers)
    assert reused.status_code == 201
