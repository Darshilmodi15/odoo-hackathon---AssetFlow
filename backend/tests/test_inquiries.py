import uuid
import pytest
from fastapi.testclient import TestClient
from app.models.inquiry import Inquiry

class TestCreateInquiry:
    def test_create_inquiry_success(self, client: TestClient, db):
        payload = {
            "name": "John Doe",
            "email": "johndoe@example.com",
            "company": "ACME Corp",
            "message": "We would like a demo of AssetFlow."
        }
        r = client.post("/api/inquiries", json=payload)
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "John Doe"
        assert data["email"] == "johndoe@example.com"
        assert data["company"] == "ACME Corp"
        assert data["message"] == "We would like a demo of AssetFlow."
        assert "id" in data

        # Check database
        inquiry_uuid = uuid.UUID(data["id"])
        inquiry_db = db.query(Inquiry).filter(Inquiry.id == inquiry_uuid).first()
        assert inquiry_db is not None
        assert inquiry_db.name == "John Doe"

    def test_create_inquiry_invalid_email(self, client: TestClient):
        # Email missing @
        payload = {
            "name": "John Doe",
            "email": "johndoeexample.com",
            "message": "Hi"
        }
        r = client.post("/api/inquiries", json=payload)
        assert r.status_code == 422

        # Email empty
        payload["email"] = ""
        r = client.post("/api/inquiries", json=payload)
        assert r.status_code == 422

    def test_create_inquiry_blank_fields(self, client: TestClient):
        # Blank name
        payload = {
            "name": "   ",
            "email": "johndoe@example.com",
            "message": "Hi"
        }
        r = client.post("/api/inquiries", json=payload)
        assert r.status_code == 422

        # Blank message
        payload = {
            "name": "John Doe",
            "email": "johndoe@example.com",
            "message": "   "
        }
        r = client.post("/api/inquiries", json=payload)
        assert r.status_code == 422
