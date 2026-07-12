"""Tests for Asset CRUD endpoints."""
import uuid
import pytest
from fastapi.testclient import TestClient

from tests.conftest import make_department, make_category, make_asset


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new_category(client: TestClient) -> str:
    name = f"TestCat-{uuid.uuid4().hex[:6]}"
    return make_category(client, name=name)["id"]


def _new_department(client: TestClient) -> str:
    name = f"Dept-{uuid.uuid4().hex[:6]}"
    code = f"D{uuid.uuid4().hex[:4].upper()}"
    return make_department(client, name=name, code=code)["id"]


def _unique_serial() -> str:
    return f"SN-{uuid.uuid4().hex[:10].upper()}"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCreateAsset:
    def test_create_asset_success(self, client: TestClient):
        cat_id = _new_category(client)
        data = make_asset(client, category_id=cat_id, name="Dell Laptop")
        assert data["name"] == "Dell Laptop"
        assert data["status"] == "available"
        assert data["tag"].startswith("AF-")
        assert "id" in data

    def test_tag_auto_generated(self, client: TestClient):
        cat_id = _new_category(client)
        a1 = make_asset(client, category_id=cat_id, serial_number=_unique_serial())
        a2 = make_asset(client, category_id=cat_id, serial_number=_unique_serial())
        assert a1["tag"] != a2["tag"]

    def test_create_asset_with_department(self, client: TestClient):
        cat_id = _new_category(client)
        dept_id = _new_department(client)
        data = make_asset(client, category_id=cat_id, department_id=dept_id)
        assert data["department_id"] == dept_id

    def test_duplicate_serial_number_returns_409(self, client: TestClient):
        cat_id = _new_category(client)
        sn = _unique_serial()
        make_asset(client, category_id=cat_id, serial_number=sn)
        r = client.post("/api/assets", json={
            "name": "Another Asset",
            "category_id": cat_id,
            "serial_number": sn,
            "location": "Office",
            "condition": "good",
            "acquisition_date": "2024-01-01",
        })
        assert r.status_code == 409
        assert r.json()["detail"]["code"] == "ASSET_SERIAL_CONFLICT"

    def test_unknown_category_returns_404(self, client: TestClient):
        r = client.post("/api/assets", json={
            "name": "Ghost Asset",
            "category_id": str(uuid.uuid4()),
            "serial_number": _unique_serial(),
            "location": "Office",
            "condition": "good",
            "acquisition_date": "2024-01-01",
        })
        assert r.status_code == 404
        assert r.json()["detail"]["code"] == "CATEGORY_NOT_FOUND"

    def test_unknown_department_returns_404(self, client: TestClient):
        cat_id = _new_category(client)
        r = client.post("/api/assets", json={
            "name": "Homeless Asset",
            "category_id": cat_id,
            "serial_number": _unique_serial(),
            "location": "Office",
            "condition": "good",
            "acquisition_date": "2024-01-01",
            "department_id": str(uuid.uuid4()),
        })
        assert r.status_code == 404
        assert r.json()["detail"]["code"] == "DEPARTMENT_NOT_FOUND"

    def test_negative_cost_returns_422(self, client: TestClient):
        cat_id = _new_category(client)
        r = client.post("/api/assets", json={
            "name": "Cheap Asset",
            "category_id": cat_id,
            "serial_number": _unique_serial(),
            "location": "Office",
            "condition": "good",
            "acquisition_date": "2024-01-01",
            "acquisition_cost": -100,
        })
        assert r.status_code == 422

    def test_invalid_condition_returns_422(self, client: TestClient):
        cat_id = _new_category(client)
        r = client.post("/api/assets", json={
            "name": "Bad Condition Asset",
            "category_id": cat_id,
            "serial_number": _unique_serial(),
            "location": "Office",
            "condition": "broken",
            "acquisition_date": "2024-01-01",
        })
        assert r.status_code == 422


class TestGetAsset:
    def test_retrieve_asset(self, client: TestClient):
        cat_id = _new_category(client)
        created = make_asset(client, category_id=cat_id)
        r = client.get(f"/api/assets/{created['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]

    def test_missing_asset_returns_404(self, client: TestClient):
        r = client.get(f"/api/assets/{uuid.uuid4()}")
        assert r.status_code == 404
        assert r.json()["detail"]["code"] == "ASSET_NOT_FOUND"


class TestListAssets:
    def test_list_returns_paginated(self, client: TestClient):
        cat_id = _new_category(client)
        make_asset(client, category_id=cat_id, serial_number=_unique_serial())
        make_asset(client, category_id=cat_id, serial_number=_unique_serial())
        r = client.get("/api/assets?skip=0&limit=5")
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert "total" in body

    def test_filter_by_status(self, client: TestClient):
        cat_id = _new_category(client)
        make_asset(client, category_id=cat_id, serial_number=_unique_serial())
        r = client.get("/api/assets?status=available")
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["status"] == "available"

    def test_filter_by_category_id(self, client: TestClient):
        cat_id = _new_category(client)
        make_asset(client, category_id=cat_id, serial_number=_unique_serial())
        r = client.get(f"/api/assets?category_id={cat_id}")
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["category_id"] == cat_id

    def test_filter_by_department_id(self, client: TestClient):
        cat_id = _new_category(client)
        dept_id = _new_department(client)
        make_asset(client, category_id=cat_id, department_id=dept_id, serial_number=_unique_serial())
        r = client.get(f"/api/assets?department_id={dept_id}")
        assert r.status_code == 200
        assert all(i["department_id"] == dept_id for i in r.json()["items"])

    def test_filter_by_is_shared(self, client: TestClient):
        cat_id = _new_category(client)
        make_asset(client, category_id=cat_id, shared=True, serial_number=_unique_serial())
        r = client.get("/api/assets?is_shared=true")
        assert r.status_code == 200
        assert all(i["shared"] is True for i in r.json()["items"])

    def test_search_by_name(self, client: TestClient):
        cat_id = _new_category(client)
        unique_name = f"UniqueAsset_{uuid.uuid4().hex[:6]}"
        make_asset(client, category_id=cat_id, name=unique_name, serial_number=_unique_serial())
        r = client.get(f"/api/assets?search={unique_name[:12]}")
        assert r.status_code == 200
        assert any(unique_name in i["name"] for i in r.json()["items"])


class TestUpdateAsset:
    def test_update_asset_name(self, client: TestClient):
        cat_id = _new_category(client)
        created = make_asset(client, category_id=cat_id)
        r = client.put(f"/api/assets/{created['id']}", json={"name": "Renamed Asset"})
        assert r.status_code == 200
        assert r.json()["name"] == "Renamed Asset"

    def test_update_with_duplicate_serial_returns_409(self, client: TestClient):
        cat_id = _new_category(client)
        sn = _unique_serial()
        make_asset(client, category_id=cat_id, serial_number=sn)
        asset2 = make_asset(client, category_id=cat_id, serial_number=_unique_serial())
        r = client.put(f"/api/assets/{asset2['id']}", json={"serial_number": sn})
        assert r.status_code == 409
        assert r.json()["detail"]["code"] == "ASSET_SERIAL_CONFLICT"

    def test_update_missing_asset_returns_404(self, client: TestClient):
        r = client.put(f"/api/assets/{uuid.uuid4()}", json={"name": "Ghost"})
        assert r.status_code == 404
        assert r.json()["detail"]["code"] == "ASSET_NOT_FOUND"


class TestPatchAssetStatus:
    def test_patch_status_to_retired(self, client: TestClient):
        cat_id = _new_category(client)
        created = make_asset(client, category_id=cat_id)
        r = client.patch(f"/api/assets/{created['id']}/status", json={"status": "retired"})
        assert r.status_code == 200
        assert r.json()["status"] == "retired"

    def test_patch_invalid_status_returns_422(self, client: TestClient):
        cat_id = _new_category(client)
        created = make_asset(client, category_id=cat_id)
        r = client.patch(f"/api/assets/{created['id']}/status", json={"status": "smashed"})
        assert r.status_code == 422
