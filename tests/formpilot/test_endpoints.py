"""Tests for FormPilot API endpoints."""
import json
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from formpilot_main import app
    return TestClient(app)


class TestHealthEndpoint:
    """GET /formpilot/health"""

    def test_health_ok(self, client):
        resp = client.get("/formpilot/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "formpilot-api"


class TestSuggestMappings:
    """POST /formpilot/suggest-mappings"""

    def test_requires_auth(self, client):
        resp = client.post("/formpilot/suggest-mappings", json={
            "fields": [{"label": "Name"}],
            "profile": {"companyName": "Test"},
        })
        assert resp.status_code == 401

    def test_returns_mappings(self, client, sample_form_fields, sample_profile):
        mock_ai_response = json.dumps([
            {"index": 0, "value": "Prodway AI"},
            {"index": 1, "value": "dale@prodway.ai"},
        ])

        from formpilot_main import app, validate_subscription
        app.dependency_overrides[validate_subscription] = lambda: {"team_id": "T1", "api_key": "pw_t"}
        try:
            with patch("formpilot_main._call_gemini", return_value=mock_ai_response):
                resp = client.post("/formpilot/suggest-mappings", json={
                    "fields": sample_form_fields,
                    "profile": sample_profile,
                })
                assert resp.status_code == 200
                data = resp.json()
                assert "mappings" in data
                assert isinstance(data["mappings"], list)
        finally:
            app.dependency_overrides = {}

    def test_empty_fields_returns_empty(self, client):
        from formpilot_main import app, validate_subscription
        app.dependency_overrides[validate_subscription] = lambda: {"team_id": "T1", "api_key": "pw_t"}
        try:
            with patch("formpilot_main._call_gemini", return_value="[]"):
                resp = client.post("/formpilot/suggest-mappings", json={
                    "fields": [],
                    "profile": {},
                })
                assert resp.status_code == 200
        finally:
            app.dependency_overrides = {}


class TestSuggestField:
    """POST /formpilot/suggest-field"""

    def test_requires_auth(self, client):
        resp = client.post("/formpilot/suggest-field", json={
            "field": {"label": "Company"},
            "profile": {"companyName": "Test"},
        })
        assert resp.status_code == 401

    def test_returns_value_and_reasoning(self, client):
        mock_response = '{"value": "Prodway AI", "reasoning": "Matches company name"}'

        from formpilot_main import app, validate_subscription
        app.dependency_overrides[validate_subscription] = lambda: {"team_id": "T1", "api_key": "pw_t"}
        try:
            with patch("formpilot_main._get_ai_provider", return_value="gemini"),                  patch("formpilot_main._call_gemini", return_value=mock_response):
                resp = client.post("/formpilot/suggest-field", json={
                    "field": {"label": "Company Name", "semanticType": "companyName"},
                    "profile": {"companyName": "Prodway AI"},
                })
                assert resp.status_code == 200
                data = resp.json()
                assert data["value"] == "Prodway AI"
                assert "reasoning" in data
        finally:
            app.dependency_overrides = {}


class TestImportFromUrl:
    """POST /formpilot/import-from-url"""

    def test_requires_auth(self, client):
        resp = client.post("/formpilot/import-from-url", json={"url": "https://example.com"})
        assert resp.status_code == 401

    def test_invalid_url_rejected(self, client):
        from formpilot_main import app, validate_subscription
        app.dependency_overrides[validate_subscription] = lambda: {"team_id": "T1", "api_key": "pw_t"}
        try:
            with patch("formpilot_main._get_ai_provider", return_value="gemini"):
                resp = client.post("/formpilot/import-from-url", json={"url": "not-a-url"})
                assert resp.status_code == 400
        finally:
            app.dependency_overrides = {}


class TestStatsEndpoints:
    """Usage stats endpoints (no auth required)."""

    def test_record_fill_no_consent(self, client):
        resp = client.post("/prodway/record-fill", json={"count": 1, "consent": False})
        assert resp.status_code == 200
        assert resp.json()["recorded"] == 0

    def test_record_sow_no_consent(self, client):
        resp = client.post("/prodway/record-sow", json={"consent": False})
        assert resp.status_code == 200
        assert resp.json()["recorded"] == 0

    def test_get_stats(self, client):
        resp = client.get("/prodway/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "forms_filled" in data
        assert "sows_sent" in data


class TestSubscriptionValidation:
    """API key validation middleware."""

    def test_missing_key_returns_401(self, client):
        resp = client.post("/formpilot/suggest-mappings", json={
            "fields": [{"label": "Test"}],
        })
        assert resp.status_code == 401
        assert "API key" in resp.json()["detail"]

    def test_bearer_auth_accepted(self, client):
        with patch("formpilot_main.httpx.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"team_id": "T1", "subscribed": True}
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            with patch("formpilot_main._call_gemini", return_value="[]"):
                # Clear cache
                from formpilot_main import _key_cache
                _key_cache.clear()

                resp = client.post(
                    "/formpilot/suggest-mappings",
                    json={"fields": [], "profile": {}},
                    headers={"Authorization": "Bearer pw_test_key_12345"},
                )
                assert resp.status_code == 200

    def test_x_api_key_header_accepted(self, client):
        with patch("formpilot_main.httpx.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"team_id": "T1", "subscribed": True}
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            with patch("formpilot_main._call_gemini", return_value="[]"):
                from formpilot_main import _key_cache
                _key_cache.clear()

                resp = client.post(
                    "/formpilot/suggest-mappings",
                    json={"fields": [], "profile": {}},
                    headers={"X-API-Key": "pw_test_key_12345"},
                )
                assert resp.status_code == 200

    def test_unsubscribed_returns_402(self, client):
        with patch("formpilot_main.httpx.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"team_id": "T1", "subscribed": False}
            mock_resp.raise_for_status = MagicMock()
            mock_get.return_value = mock_resp

            from formpilot_main import _key_cache
            _key_cache.clear()

            resp = client.post(
                "/formpilot/suggest-mappings",
                json={"fields": [], "profile": {}},
                headers={"X-API-Key": "pw_test_key_12345"},
            )
            assert resp.status_code == 402

    def test_fail_open_for_pw_keys_during_outage(self, client):
        import httpx as real_httpx
        with patch("formpilot_main.httpx.get", side_effect=real_httpx.RequestError("connection refused")):
            with patch("formpilot_main._call_gemini", return_value="[]"):
                from formpilot_main import _key_cache
                _key_cache.clear()

                resp = client.post(
                    "/formpilot/suggest-mappings",
                    json={"fields": [], "profile": {}},
                    headers={"X-API-Key": "pw_valid_format_key"},
                )
                assert resp.status_code == 200
