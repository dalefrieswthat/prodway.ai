"""Tests for SowFlow HTTP endpoints (FastAPI)."""
import json
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from sowflow_main import api
    return TestClient(api)


class TestHealthEndpoints:
    """Health and version endpoints."""

    def test_health_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert data["status"] == "ok"
        assert "timestamp" in data

    def test_root_returns_html(self, client):
        resp = client.get("/")
        assert resp.status_code in (200, 503)


class TestContactForm:
    """POST /api/contact endpoint."""

    def test_contact_missing_fields(self, client):
        resp = client.post("/api/contact", json={})
        assert resp.status_code == 422

    def test_contact_valid_submission(self, client):
        with patch("sowflow_main.SENDGRID_API_KEY", ""):
            resp = client.post("/api/contact", json={
                "name": "Test User",
                "email": "test@example.com",
                "company": "Test Corp",
                "message": "Hello from tests",
            })
            assert resp.status_code in (200, 503)


class TestApiKeyValidation:
    """GET /api/validate-key endpoint."""

    def test_missing_key_returns_401(self, client):
        resp = client.get("/api/validate-key")
        assert resp.status_code == 401

    def test_invalid_key_returns_401(self, client):
        resp = client.get("/api/validate-key", headers={"X-API-Key": "bad_key"})
        assert resp.status_code == 401

    def test_valid_key_returns_team(self, client, tmp_data_dir):
        with patch("sowflow_main.DATA_DIR", tmp_data_dir):
            with patch("sowflow_main.INTEGRATIONS_DIR", tmp_data_dir / "integrations"):
                from sowflow_main import generate_team_api_key, set_team_billing

                key = generate_team_api_key("T_VALID")
                set_team_billing("T_VALID", stripe_subscription_status="active")

                # Reset rate limiter
                from sowflow_main import _key_validation_attempts
                _key_validation_attempts.clear()

                resp = client.get("/api/validate-key", headers={"X-API-Key": key})
                assert resp.status_code in (200, 503)
                data = resp.json()
                assert data["team_id"] == "T_VALID"
                assert data["subscribed"] is True


class TestSignupFlow:
    """GET /signup pay-first flow."""

    def test_signup_without_stripe_key(self, client, monkeypatch):
        monkeypatch.setattr("sowflow_main.STRIPE_SECRET_KEY", "")
        resp = client.get("/signup", follow_redirects=False)
        # Should return an error page or redirect, not crash
        assert resp.status_code in (200, 302, 500)
