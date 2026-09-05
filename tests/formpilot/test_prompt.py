"""Tests for FormPilot AI prompt construction."""
import json

import pytest


class TestBuildPrompt:
    """Prompt construction for AI field mapping."""

    def test_basic_prompt_structure(self, sample_form_fields, sample_profile):
        from formpilot_main import build_prompt

        prompt = build_prompt(sample_form_fields, sample_profile, None)
        assert "form-fill assistant" in prompt
        assert "Company profile" in prompt
        assert "JSON array" in prompt

    def test_includes_field_labels(self, sample_form_fields, sample_profile):
        from formpilot_main import build_prompt

        prompt = build_prompt(sample_form_fields, sample_profile, None)
        assert "Company Name" in prompt
        assert "Email" in prompt
        assert "LinkedIn URL" in prompt

    def test_includes_profile_data(self, sample_form_fields, sample_profile):
        from formpilot_main import build_prompt

        prompt = build_prompt(sample_form_fields, sample_profile, None)
        assert "Prodway AI" in prompt
        assert "dale@prodway.ai" in prompt

    def test_includes_context_when_provided(self, sample_form_fields, sample_profile):
        from formpilot_main import build_prompt

        context = "We build AI tools for consulting firms. YC S24 batch. $2M ARR."
        prompt = build_prompt(sample_form_fields, sample_profile, context)
        assert "AI tools for consulting" in prompt
        assert "company context" in prompt.lower()

    def test_no_context_block_when_none(self, sample_form_fields, sample_profile):
        from formpilot_main import build_prompt

        prompt = build_prompt(sample_form_fields, sample_profile, None)
        assert "company context" not in prompt.lower() or "User also provided" not in prompt

    def test_truncates_long_context(self, sample_form_fields, sample_profile):
        from formpilot_main import build_prompt

        long_context = "a" * 20000
        prompt = build_prompt(sample_form_fields, sample_profile, long_context)
        # Context should be truncated to 12000 chars
        assert len(prompt) < 25000

    def test_includes_semantic_types(self, sample_form_fields, sample_profile):
        from formpilot_main import build_prompt

        prompt = build_prompt(sample_form_fields, sample_profile, None)
        assert "companyName" in prompt
        assert "email" in prompt

    def test_prefilled_fields_noted(self, sample_profile):
        from formpilot_main import build_prompt

        fields_with_values = [
            {"label": "Company", "semanticType": "companyName", "value": "Already Filled"},
            {"label": "Email", "semanticType": "email", "value": ""},
        ]
        prompt = build_prompt(fields_with_values, sample_profile, None)
        assert "Already Filled" in prompt
        assert "already filled" in prompt.lower() or "currentValue" in prompt

    def test_empty_fields_list(self, sample_profile):
        from formpilot_main import build_prompt

        prompt = build_prompt([], sample_profile, None)
        assert "form-fill assistant" in prompt

    def test_empty_profile(self, sample_form_fields):
        from formpilot_main import build_prompt

        prompt = build_prompt(sample_form_fields, {}, None)
        assert "Form fields" in prompt


class TestStripHtml:
    """HTML stripping for URL import."""

    def test_removes_html_tags(self):
        from formpilot_main import _strip_html
        assert _strip_html("<p>Hello <b>world</b></p>") == "Hello world"

    def test_removes_script_tags(self):
        from formpilot_main import _strip_html
        result = _strip_html("<script>alert('xss')</script><p>Safe content</p>")
        assert "alert" not in result
        assert "Safe content" in result

    def test_removes_style_tags(self):
        from formpilot_main import _strip_html
        result = _strip_html("<style>.red{color:red}</style><p>Visible</p>")
        assert "color:red" not in result
        assert "Visible" in result

    def test_truncates_long_content(self):
        from formpilot_main import _strip_html
        long_html = "<p>" + "x" * 20000 + "</p>"
        result = _strip_html(long_html)
        assert len(result) <= 15000

    def test_collapses_whitespace(self):
        from formpilot_main import _strip_html
        result = _strip_html("<p>Hello</p>\n\n\n<p>World</p>")
        assert "  " not in result or result.count(" ") < 5


class TestAiProviderSelection:
    """AI provider resolution."""

    def test_gemini_when_google_key_set(self):
        import formpilot_main
        original = formpilot_main.GOOGLE_API_KEY
        try:
            formpilot_main.GOOGLE_API_KEY = "test-key"
            assert formpilot_main._get_ai_provider() == "gemini"
        finally:
            formpilot_main.GOOGLE_API_KEY = original

    def test_none_when_no_keys(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        import main as mod
        mod.GOOGLE_API_KEY = ""
        result = mod._get_ai_provider()
        assert result == "none"
