"""Tests for Department CRUD endpoints."""
import uuid
import pytest
from fastapi.testclient import TestClient

from tests.conftest import make_department


class TestCreateDepartment:
    def test_create_department_success(self, client: TestClient):
        data = make_department(client, name="Information Technology", code="IT")
        assert data["name"] == "Information Technology"
        assert data["code"] == "IT"
        assert data["status"] == "active"
        assert "id" in data

    def test_code_normalised_to_uppercase(self, client: TestClient):
        data = make_department(client, name="Human Resources", code="hr")
        assert data["code"] == "HR"

    def test_duplicate_code_returns_409(self, client: TestClient):
        make_department(client, name="Finance", code="FIN")
        r = client.post("/api/departments", json={"name": "Finance2", "code": "FIN"})
        assert r.status_code == 409
        body = r.json()
        assert body["detail"]["code"] == "DEPARTMENT_CODE_CONFLICT"

    def test_duplicate_name_returns_409(self, client: TestClient):
        make_department(client, name="Operations", code="OPS")
        r = client.post("/api/departments", json={"name": "Operations", "code": "OPS2"})
        assert r.status_code == 409
        body = r.json()
        assert body["detail"]["code"] == "DEPARTMENT_NAME_CONFLICT"

    def test_blank_name_returns_422(self, client: TestClient):
        r = client.post("/api/departments", json={"name": "  ", "code": "BLANK"})
        assert r.status_code == 422

    def test_invalid_status_returns_422(self, client: TestClient):
        r = client.post("/api/departments", json={"name": "Test", "code": "TST", "status": "unknown"})
        assert r.status_code == 422


class TestGetDepartment:
    def test_retrieve_department(self, client: TestClient):
        created = make_department(client, name="Administration", code="ADM")
        r = client.get(f"/api/departments/{created['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]

    def test_missing_department_returns_404(self, client: TestClient):
        r = client.get(f"/api/departments/{uuid.uuid4()}")
        assert r.status_code == 404
        body = r.json()
        assert body["detail"]["code"] == "DEPARTMENT_NOT_FOUND"


class TestListDepartments:
    def test_list_returns_paginated(self, client: TestClient):
        make_department(client, name="Dept Alpha", code="ALPHA")
        make_department(client, name="Dept Beta", code="BETA")
        r = client.get("/api/departments?skip=0&limit=10")
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert "total" in body

    def test_filter_by_status(self, client: TestClient):
        make_department(client, name="Active Dept", code="ACTD")
        r = client.get("/api/departments?status=active")
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["status"] == "active"

    def test_search_by_name(self, client: TestClient):
        make_department(client, name="Unique Search Dept", code="USD")
        r = client.get("/api/departments?search=Unique+Search")
        assert r.status_code == 200
        assert any("Unique Search" in i["name"] for i in r.json()["items"])


class TestUpdateDepartment:
    def test_update_department_name(self, client: TestClient):
        created = make_department(client, name="Old Name", code="OLD")
        r = client.put(f"/api/departments/{created['id']}", json={"name": "New Name"})
        assert r.status_code == 200
        assert r.json()["name"] == "New Name"

    def test_update_with_invalid_parent_id_returns_error(self, client: TestClient):
        created = make_department(client, name="Child Dept", code="CHLD")
        r = client.put(
            f"/api/departments/{created['id']}",
            json={"parent_id": str(uuid.uuid4())},
        )
        assert r.status_code in (400, 404)
        body = r.json()
        assert body["detail"]["code"] == "INVALID_PARENT_DEPARTMENT"

    def test_department_cannot_be_own_parent(self, client: TestClient):
        created = make_department(client, name="Solo Dept", code="SOLO")
        r = client.put(
            f"/api/departments/{created['id']}",
            json={"parent_id": created["id"]},
        )
        assert r.status_code == 400
        assert r.json()["detail"]["code"] == "INVALID_PARENT_DEPARTMENT"

    def test_update_missing_department_returns_404(self, client: TestClient):
        r = client.put(f"/api/departments/{uuid.uuid4()}", json={"name": "Ghost"})
        assert r.status_code == 404


class TestPatchDepartmentStatus:
    def test_patch_status_to_inactive(self, client: TestClient):
        created = make_department(client, name="Toggle Dept", code="TOG")
        r = client.patch(f"/api/departments/{created['id']}/status", json={"status": "inactive"})
        assert r.status_code == 200
        assert r.json()["status"] == "inactive"

    def test_patch_invalid_status_returns_422(self, client: TestClient):
        created = make_department(client, name="Status Dept", code="STD")
        r = client.patch(f"/api/departments/{created['id']}/status", json={"status": "deleted"})
        assert r.status_code == 422
