"""Tests for SowFlow file-based storage layer."""
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest


class TestSowStorage:
    """SOW CRUD operations on file-based storage."""

    def test_save_and_load_sow(self, tmp_data_dir, sample_sow):
        with patch("sowflow_main.DATA_DIR", tmp_data_dir):
            from sowflow_main import save_sow, load_sow

            save_sow("test-001", sample_sow)
            loaded = load_sow("test-001")

            assert loaded is not None
            assert loaded["id"] == "test-001"
            assert loaded["title"] == "Kubernetes Migration"
            assert loaded["pricing"]["total"] == 35000
            assert "updated_at" in loaded

    def test_load_nonexistent_sow(self, tmp_data_dir):
        with patch("sowflow_main.DATA_DIR", tmp_data_dir):
            from sowflow_main import load_sow

            assert load_sow("nonexistent") is None

    def test_save_sow_overwrites(self, tmp_data_dir, sample_sow):
        with patch("sowflow_main.DATA_DIR", tmp_data_dir):
            from sowflow_main import save_sow, load_sow

            save_sow("test-002", sample_sow)
            sample_sow["title"] = "Updated Title"
            save_sow("test-002", sample_sow)

            loaded = load_sow("test-002")
            assert loaded["title"] == "Updated Title"

    def test_list_sows_empty(self, tmp_data_dir):
        with patch("sowflow_main.DATA_DIR", tmp_data_dir):
            from sowflow_main import list_sows

            assert list_sows() == []

    def test_list_sows_returns_all(self, tmp_data_dir, sample_sow):
        with patch("sowflow_main.DATA_DIR", tmp_data_dir):
            from sowflow_main import save_sow, list_sows

            for i in range(3):
                sow = {**sample_sow, "created_at": f"2026-04-0{i+1}T00:00:00"}
                save_sow(f"sow-{i}", sow)

            result = list_sows()
            assert len(result) == 3

    def test_list_sows_filters_by_team(self, tmp_data_dir, sample_sow):
        with patch("sowflow_main.DATA_DIR", tmp_data_dir):
            from sowflow_main import save_sow, list_sows

            sow_a = {**sample_sow, "_team_id": "TEAM_A", "created_at": "2026-04-01T00:00:00"}
            sow_b = {**sample_sow, "_team_id": "TEAM_B", "created_at": "2026-04-02T00:00:00"}
            save_sow("sow-a", sow_a)
            save_sow("sow-b", sow_b)

            result = list_sows(team_id="TEAM_A")
            assert len(result) == 1
            assert result[0]["_team_id"] == "TEAM_A"

    def test_list_sows_sorted_by_date_descending(self, tmp_data_dir, sample_sow):
        with patch("sowflow_main.DATA_DIR", tmp_data_dir):
            from sowflow_main import save_sow, list_sows

            for day in [3, 1, 2]:
                sow = {**sample_sow, "created_at": f"2026-04-0{day}T00:00:00"}
                save_sow(f"sow-{day}", sow)

            result = list_sows()
            dates = [s["created_at"] for s in result]
            assert dates == sorted(dates, reverse=True)


class TestTeamIntegrations:
    """Per-team integration credential storage."""

    def test_save_and_load(self, tmp_data_dir):
        with patch("sowflow_main.INTEGRATIONS_DIR", tmp_data_dir / "integrations"):
            from sowflow_main import save_team_integrations, load_team_integrations

            save_team_integrations("T001", {"stripe_account_id": "acct_123"})
            result = load_team_integrations("T001")

            assert result["stripe_account_id"] == "acct_123"
            assert "updated_at" in result

    def test_merge_update(self, tmp_data_dir):
        with patch("sowflow_main.INTEGRATIONS_DIR", tmp_data_dir / "integrations"):
            from sowflow_main import save_team_integrations, load_team_integrations

            save_team_integrations("T002", {"key_a": "val_a"})
            save_team_integrations("T002", {"key_b": "val_b"})

            result = load_team_integrations("T002")
            assert result["key_a"] == "val_a"
            assert result["key_b"] == "val_b"

    def test_load_nonexistent_team(self, tmp_data_dir):
        with patch("sowflow_main.INTEGRATIONS_DIR", tmp_data_dir / "integrations"):
            from sowflow_main import load_team_integrations

            assert load_team_integrations("T_MISSING") == {}


class TestEditTracking:
    """SOW edit tracking for data moat."""

    def test_save_edit(self, tmp_data_dir):
        with patch("sowflow_main.EDITS_DIR", tmp_data_dir / "edits"):
            from sowflow_main import save_edit

            save_edit("sow-001", "T001", "U001", "title", "Old Title", "New Title")

            edits = list((tmp_data_dir / "edits").glob("sow-001_*.json"))
            assert len(edits) == 1
            data = json.loads(edits[0].read_text())
            assert data["field_name"] == "title"
            assert data["old_value"] == "Old Title"
            assert data["new_value"] == "New Title"

    def test_generation_metadata(self, tmp_data_dir):
        with patch("sowflow_main.GENERATIONS_DIR", tmp_data_dir / "generations"):
            from sowflow_main import save_generation_metadata, mark_generation_edited

            class MockResponse:
                model = "gemma-3-4b-it"
                usage = type("U", (), {"input_tokens": 500, "output_tokens": 1000})()

            save_generation_metadata("sow-002", "T001", MockResponse(), 3500)

            path = tmp_data_dir / "generations" / "sow-002.json"
            assert path.exists()
            data = json.loads(path.read_text())
            assert data["model"] == "gemma-3-4b-it"
            assert data["generation_time_ms"] == 3500
            assert data["was_edited"] is False

            mark_generation_edited("sow-002", ["title", "scope"])
            data = json.loads(path.read_text())
            assert data["was_edited"] is True
            assert data["edit_count"] == 2
            assert set(data["fields_edited"]) == {"title", "scope"}


class TestOutcomes:
    """Deal outcome tracking."""

    def test_save_outcome(self, tmp_data_dir):
        with patch("sowflow_main.OUTCOMES_DIR", tmp_data_dir / "outcomes"):
            from sowflow_main import save_outcome

            save_outcome("sow-003", "T001", "signed", signed_at="2026-04-01")

            path = tmp_data_dir / "outcomes" / "sow-003.json"
            assert path.exists()
            data = json.loads(path.read_text())
            assert data["outcome"] == "signed"
            assert data["signed_at"] == "2026-04-01"
