"""Pytest configuration and shared fixtures for AssetFlow backend tests.

Strategy: each test runs inside a SQLite database. Auth is bypassed by
monkey-patching `deps.check_role` so every role check passes, and by
overriding `get_current_user` with a dummy admin user.
"""
import uuid
# pyrefly: ignore [missing-import]
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

# SQLite compatibility patch for postgresql.UUID
from sqlalchemy.dialects import postgresql
from app.db.base import GUID
class SQLiteUUID(GUID):
    cache_ok = True
    def __init__(self, *args, **kwargs):
        kwargs.pop("as_uuid", None)
        super().__init__(*args, **kwargs)
postgresql.UUID = SQLiteUUID

from app.main import app
from app.db.session import get_session
from app.db.base import Base
from app.models.user import User
from app.models.organization import Department, AssetCategory
from app.models.asset import Asset
from app.api import deps


# ---------------------------------------------------------------------------
# SQLite engine – isolated per test session
# ---------------------------------------------------------------------------

SQLALCHEMY_TEST_URL = "sqlite:///./test_assetflow.db"

test_engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
)

# Enable FK enforcement in SQLite
@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# ---------------------------------------------------------------------------
# Create / drop tables once per session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


# ---------------------------------------------------------------------------
# Per-test rollback session
# ---------------------------------------------------------------------------

@pytest.fixture()
def db():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    # Seed a single admin user so get_current_user fallback returns it
    admin = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name="Test Admin",
        email="admin@test.local",
        hashed_password="$2b$12$fakehash",
        role="admin",
        status="active",
    )
    session.add(admin)
    session.flush()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ---------------------------------------------------------------------------
# TestClient with overrides
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(db: Session) -> TestClient:
    def override_get_session():
        yield db

    def get_test_user():
        return db.query(User).filter(
            User.id == uuid.UUID("00000000-0000-0000-0000-000000000001")
        ).first()

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[deps.get_current_user] = get_test_user

    # Monkey-patch check_role so every call to deps.check_role([...]) returns
    # a FastAPI dependency function that resolves to our test admin.
    import app.api.deps as _deps
    _original_check_role = _deps.check_role
    _deps.check_role = lambda roles: get_test_user  # type: ignore

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides.clear()
    _deps.check_role = _original_check_role


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

def make_department(client: TestClient, *, name: str, code: str, **kwargs) -> dict:
    r = client.post("/api/departments", json={"name": name, "code": code, **kwargs})
    assert r.status_code == 201, f"Create dept failed: {r.text}"
    return r.json()


def make_category(client: TestClient, *, name: str, **kwargs) -> dict:
    r = client.post("/api/categories", json={"name": name, **kwargs})
    assert r.status_code == 201, f"Create category failed: {r.text}"
    return r.json()


def make_asset(client: TestClient, *, category_id: str, **kwargs) -> dict:
    payload = {
        "name": kwargs.pop("name", "Test Asset"),
        "category_id": category_id,
        "serial_number": kwargs.pop("serial_number", f"SN-TEST-{uuid.uuid4().hex[:6]}"),
        "location": kwargs.pop("location", "Test Location"),
        "condition": kwargs.pop("condition", "good"),
        "acquisition_date": kwargs.pop("acquisition_date", "2024-01-01"),
        **kwargs,
    }
    r = client.post("/api/assets", json=payload)
    assert r.status_code == 201, f"Create asset failed: {r.text}"
    return r.json()
