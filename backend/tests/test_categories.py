"""Tests for Asset Category CRUD endpoints."""
import uuid
import pytest
from fastapi.testclient import TestClient

from tests.conftest import make_category


class TestCreateCategory:
    def test_create_category_success(self, client: TestClient):
        data = make_category(client, name="Electronics", description="Laptops etc.")
        assert data["name"] == "Electronics"
        assert data["status"] == "active"
        assert "id" in data
        assert "created_at" in data

    def test_create_category_no_description(self, client: TestClient):
        data = make_category(client, name="Furniture")
        assert data["description"] is None

    def test_duplicate_name_returns_409(self, client: TestClient):
        make_category(client, name="Vehicles")
        r = client.post("/api/categories", json={"name": "Vehicles"})
        assert r.status_code == 409
        assert r.json()["detail"]["code"] == "CATEGORY_NAME_CONFLICT"

    def test_blank_name_returns_422(self, client: TestClient):
        r = client.post("/api/categories", json={"name": "   "})
        assert r.status_code == 422

    def test_invalid_status_returns_422(self, client: TestClient):
        r = client.post("/api/categories", json={"name": "Rooms", "status": "pending"})
        assert r.status_code == 422


class TestGetCategory:
    def test_retrieve_category(self, client: TestClient):
        created = make_category(client, name="Equipment")
        r = client.get(f"/api/categories/{created['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]

    def test_missing_category_returns_404(self, client: TestClient):
        r = client.get(f"/api/categories/{uuid.uuid4()}")
        assert r.status_code == 404
        assert r.json()["detail"]["code"] == "CATEGORY_NOT_FOUND"


class TestListCategories:
    def test_list_returns_paginated(self, client: TestClient):
        make_category(client, name="Cat A")
        make_category(client, name="Cat B")
        r = client.get("/api/categories?skip=0&limit=10")
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert body["limit"] == 10

    def test_filter_by_status(self, client: TestClient):
        make_category(client, name="Active Cat")
        r = client.get("/api/categories?status=active")
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["status"] == "active"

    def test_search_by_name(self, client: TestClient):
        make_category(client, name="Unique Category XYZ")
        r = client.get("/api/categories?search=Unique+Category+XYZ")
        assert r.status_code == 200
        assert any("Unique" in i["name"] for i in r.json()["items"])


class TestUpdateCategory:
    def test_update_category_name(self, client: TestClient):
        created = make_category(client, name="Old Category")
        r = client.put(f"/api/categories/{created['id']}", json={"name": "New Category"})
        assert r.status_code == 200
        assert r.json()["name"] == "New Category"

    def test_update_with_duplicate_name_returns_409(self, client: TestClient):
        make_category(client, name="Alpha Cat")
        created = make_category(client, name="Beta Cat")
        r = client.put(f"/api/categories/{created['id']}", json={"name": "Alpha Cat"})
        assert r.status_code == 409
        assert r.json()["detail"]["code"] == "CATEGORY_NAME_CONFLICT"

    def test_update_missing_category_returns_404(self, client: TestClient):
        r = client.put(f"/api/categories/{uuid.uuid4()}", json={"name": "Ghost"})
        assert r.status_code == 404


class TestPatchCategoryStatus:
    def test_patch_status_to_inactive(self, client: TestClient):
        created = make_category(client, name="Toggle Category")
        r = client.patch(f"/api/categories/{created['id']}/status", json={"status": "inactive"})
        assert r.status_code == 200
        assert r.json()["status"] == "inactive"

    def test_patch_invalid_status_returns_422(self, client: TestClient):
        created = make_category(client, name="Status Category")
        r = client.patch(f"/api/categories/{created['id']}/status", json={"status": "archived"})
        assert r.status_code == 422
