"""Tests for SowFlow billing, subscription, and API key management."""
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestSubscriptionChecks:
    """Subscription status checks."""

    def test_team_subscribed_active(self, tmp_data_dir):
        with patch("sowflow_main.INTEGRATIONS_DIR", tmp_data_dir / "integrations"):
            from sowflow_main import is_team_subscribed, set_team_billing

            set_team_billing("T001", stripe_subscription_status="active")
            assert is_team_subscribed("T001") is True

    def test_team_not_subscribed_no_record(self, tmp_data_dir):
        with patch("sowflow_main.INTEGRATIONS_DIR", tmp_data_dir / "integrations"):
            from sowflow_main import is_team_subscribed

            assert is_team_subscribed("T_NONE") is False

    def test_team_not_subscribed_canceled(self, tmp_data_dir):
        with patch("sowflow_main.INTEGRATIONS_DIR", tmp_data_dir / "integrations"):
            from sowflow_main import is_team_subscribed, set_team_billing

            set_team_billing("T002", stripe_subscription_status="canceled")
            assert is_team_subscribed("T002") is False

    def test_team_subscribed_case_insensitive(self, tmp_data_dir):
        with patch("sowflow_main.INTEGRATIONS_DIR", tmp_data_dir / "integrations"):
            from sowflow_main import is_team_subscribed, set_team_billing

            set_team_billing("T003", stripe_subscription_status="Active")
            assert is_team_subscribed("T003") is True


class TestCanTeamGenerateSow:
    """Paywall enforcement for SOW generation."""

    def test_active_subscription_allowed(self, tmp_data_dir):
        with patch("sowflow_main.INTEGRATIONS_DIR", tmp_data_dir / "integrations"):
            from sowflow_main import can_team_generate_sow, set_team_billing

            set_team_billing("T010", stripe_subscription_status="active")
            allowed, msg = can_team_generate_sow("T010")
            assert allowed is True
            assert msg == ""

    def test_no_subscription_blocked(self, tmp_data_dir):
        with patch("sowflow_main.INTEGRATIONS_DIR", tmp_data_dir / "integrations"):
            from sowflow_main import can_team_generate_sow

            allowed, msg = can_team_generate_sow("T_NEW")
            assert allowed is False
            assert "subscription" in msg.lower()
            assert "$5/mo" in msg


class TestApiKeyManagement:
    """Prodway API key generation and lookup."""

    def test_generate_api_key_format(self, tmp_data_dir):
        with patch("sowflow_main.INTEGRATIONS_DIR", tmp_data_dir / "integrations"):
            from sowflow_main import generate_team_api_key

            key = generate_team_api_key("T020")
            assert key.startswith("pw_")
            assert len(key) > 35

    def test_get_team_api_key(self, tmp_data_dir):
        with patch("sowflow_main.INTEGRATIONS_DIR", tmp_data_dir / "integrations"):
            from sowflow_main import generate_team_api_key, get_team_api_key

            key = generate_team_api_key("T021")
            retrieved = get_team_api_key("T021")
            assert retrieved == key

    def test_get_team_api_key_none(self, tmp_data_dir):
        with patch("sowflow_main.INTEGRATIONS_DIR", tmp_data_dir / "integrations"):
            from sowflow_main import get_team_api_key

            assert get_team_api_key("T_NOKEY") is None

    def test_get_team_by_api_key(self, tmp_data_dir):
        with patch("sowflow_main.DATA_DIR", tmp_data_dir),              patch("sowflow_main.INTEGRATIONS_DIR", tmp_data_dir / "integrations"):
            from sowflow_main import generate_team_api_key, get_team_by_api_key

            key = generate_team_api_key("T022")
            found = get_team_by_api_key(key)
            assert found == "T022"

    def test_get_team_by_invalid_key(self, tmp_data_dir):
        with patch("sowflow_main.DATA_DIR", tmp_data_dir):
            from sowflow_main import get_team_by_api_key

            assert get_team_by_api_key("invalid_key") is None
            assert get_team_by_api_key("") is None
            assert get_team_by_api_key("pw_nonexistent") is None

    def test_regenerate_overwrites(self, tmp_data_dir):
        with patch("sowflow_main.INTEGRATIONS_DIR", tmp_data_dir / "integrations"):
            from sowflow_main import generate_team_api_key, get_team_api_key

            key1 = generate_team_api_key("T023")
            key2 = generate_team_api_key("T023")
            assert key1 != key2
            assert get_team_api_key("T023") == key2


class TestSowUsageCounting:
    """Monthly SOW usage counting for metered billing."""

    def test_count_this_month_empty(self, tmp_data_dir):
        with patch("sowflow_main.DATA_DIR", tmp_data_dir):
            from sowflow_main import get_sow_count_this_month

            assert get_sow_count_this_month("T030") == 0

    def test_count_this_month_with_sows(self, tmp_data_dir):
        from datetime import datetime
        with patch("sowflow_main.DATA_DIR", tmp_data_dir):
            from sowflow_main import save_sow, get_sow_count_this_month

            now = datetime.now()
            for i in range(3):
                sow = {
                    "_team_id": "T031",
                    "title": f"SOW {i}",
                    "created_at": now.isoformat(),
                }
                save_sow(f"sow-{i}", sow)

            assert get_sow_count_this_month("T031") == 3

    def test_count_excludes_other_teams(self, tmp_data_dir):
        from datetime import datetime
        with patch("sowflow_main.DATA_DIR", tmp_data_dir):
            from sowflow_main import save_sow, get_sow_count_this_month

            now = datetime.now()
            save_sow("sow-a", {"_team_id": "T032", "title": "A", "created_at": now.isoformat()})
            save_sow("sow-b", {"_team_id": "T033", "title": "B", "created_at": now.isoformat()})

            assert get_sow_count_this_month("T032") == 1


class TestRateLimiting:
    """Rate limiting for API key validation."""

    def test_allows_under_limit(self):
        from sowflow_main import _check_rate_limit, _key_validation_attempts
        _key_validation_attempts.clear()

        for _ in range(5):
            assert _check_rate_limit("T_RATE") is True

    def test_blocks_over_limit(self):
        from sowflow_main import _check_rate_limit, _key_validation_attempts
        _key_validation_attempts.clear()

        for _ in range(5):
            _check_rate_limit("T_RATE2")

        assert _check_rate_limit("T_RATE2") is False
