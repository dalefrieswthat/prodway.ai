"""Tests for SOW generation and Slack formatting."""
import json
import re
from unittest.mock import patch, MagicMock

import pytest


class TestSowGeneration:
    """AI-powered SOW generation."""

    def test_generate_sow_returns_tuple(self):
        """generate_sow returns (sow_dict, response, time_ms)."""
        mock_response = json.dumps({
            "title": "Test Project",
            "executive_summary": "A test SOW.",
            "scope": ["Item 1"],
            "deliverables": ["Output 1"],
            "timeline": [{"phase": "Phase 1", "duration": "1 week", "description": "Do stuff"}],
            "pricing": {"total": 10000, "currency": "USD", "structure": "50/50"},
        })

        with patch("sowflow_main._resolve_ai_provider") as mock_resolve:
            with patch("sowflow_main._call_gemini") as mock_gemini:
                mock_resolve.return_value = ("gemini", None)
                mock_gemini.return_value = (mock_response, {"input_tokens": 100, "output_tokens": 200})

                from sowflow_main import generate_sow
                sow, response, time_ms = generate_sow("Build a website")

                assert sow["title"] == "Test Project"
                assert sow["pricing"]["total"] == 10000
                assert isinstance(time_ms, int)

    def test_generate_sow_handles_markdown_json(self):
        """SOW generation handles JSON wrapped in markdown code blocks."""
        mock_response = '```json\n{"title": "Wrapped", "executive_summary": "test", "scope": [], "deliverables": [], "timeline": [], "pricing": {"total": 5000, "currency": "USD", "structure": "TBD"}}\n```'

        with patch("sowflow_main._resolve_ai_provider") as mock_resolve:
            with patch("sowflow_main._call_gemini") as mock_gemini:
                mock_resolve.return_value = ("gemini", None)
                mock_gemini.return_value = (mock_response, {"input_tokens": 50, "output_tokens": 100})

                from sowflow_main import generate_sow
                sow, _, _ = generate_sow("Simple project")

                assert sow["title"] == "Wrapped"

    def test_generate_sow_handles_invalid_json(self):
        """SOW generation falls back gracefully on invalid JSON."""
        with patch("sowflow_main._resolve_ai_provider") as mock_resolve:
            with patch("sowflow_main._call_gemini") as mock_gemini:
                mock_resolve.return_value = ("gemini", None)
                mock_gemini.return_value = ("This is not JSON at all", {"input_tokens": 50, "output_tokens": 50})

                from sowflow_main import generate_sow
                sow, _, _ = generate_sow("Bad response test")

                assert sow["title"] == "Project Proposal"
                assert "TBD" in str(sow["timeline"])


class TestSlackFormatting:
    """Slack Block Kit formatting for SOW display."""

    def test_format_sow_produces_blocks(self, sample_sow):
        from sowflow_main import format_sow_for_slack

        blocks = format_sow_for_slack(sample_sow, "sow-fmt-001")
        assert isinstance(blocks, list)
        assert len(blocks) > 5

        block_types = [b["type"] for b in blocks]
        assert "header" in block_types
        assert "section" in block_types
        assert "actions" in block_types

    def test_format_includes_pricing(self, sample_sow):
        from sowflow_main import format_sow_for_slack

        blocks = format_sow_for_slack(sample_sow, "sow-fmt-002")
        all_text = json.dumps(blocks)
        assert "35,000" in all_text or "35000" in all_text

    def test_format_includes_action_buttons(self, sample_sow):
        from sowflow_main import format_sow_for_slack

        blocks = format_sow_for_slack(sample_sow, "sow-fmt-003")
        action_blocks = [b for b in blocks if b.get("type") == "actions"]
        assert len(action_blocks) >= 1

        action_ids = []
        for ab in action_blocks:
            for elem in ab.get("elements", []):
                action_ids.append(elem.get("action_id", ""))

        assert "send_sow" in action_ids
        assert "edit_sow" in action_ids
        assert "dismiss_sow" in action_ids

    def test_format_handles_empty_sections(self):
        from sowflow_main import format_sow_for_slack

        minimal = {
            "title": "Minimal SOW",
            "executive_summary": "Just a summary.",
            "pricing": {"total": 0, "structure": "TBD"},
        }
        blocks = format_sow_for_slack(minimal, "sow-min-001")
        assert isinstance(blocks, list)
        assert len(blocks) >= 3


class TestSowHtmlGeneration:
    """SOW to HTML conversion for DocuSign envelopes."""

    def test_generate_sow_html(self, sample_sow):
        from sowflow_main import generate_sow_html

        html = generate_sow_html(sample_sow, "John Smith", "Acme Corp")
        assert "Kubernetes Migration" in html
        assert "Acme Corp" in html or "John Smith" in html
        assert "$35,000" in html or "35,000" in html
        assert "<!DOCTYPE html>" in html or "<html" in html
