"""Tests for FormPilot field validation rules."""
import pytest


class TestLooksLikeUrl:
    """URL detection helper."""

    def test_https_url(self):
        from formpilot_main import _looks_like_url
        assert _looks_like_url("https://example.com") is True

    def test_http_url(self):
        from formpilot_main import _looks_like_url
        assert _looks_like_url("http://example.com/path") is True

    def test_domain_pattern(self):
        from formpilot_main import _looks_like_url
        assert _looks_like_url("example.com") is True

    def test_plain_text_not_url(self):
        from formpilot_main import _looks_like_url
        assert _looks_like_url("just a name") is False

    def test_empty_not_url(self):
        from formpilot_main import _looks_like_url
        assert _looks_like_url("") is False

    def test_very_long_not_url(self):
        from formpilot_main import _looks_like_url
        assert _looks_like_url("x" * 2001) is False


class TestLooksLikeLinkedinUrl:
    """LinkedIn URL detection."""

    def test_full_linkedin_url(self):
        from formpilot_main import _looks_like_linkedin_url
        assert _looks_like_linkedin_url("https://linkedin.com/company/prodway") is True

    def test_linkedin_without_protocol(self):
        from formpilot_main import _looks_like_linkedin_url
        assert _looks_like_linkedin_url("linkedin.com/in/dale") is True

    def test_plain_name_not_linkedin(self):
        from formpilot_main import _looks_like_linkedin_url
        assert _looks_like_linkedin_url("Dale Yarborough") is False

    def test_empty_not_linkedin(self):
        from formpilot_main import _looks_like_linkedin_url
        assert _looks_like_linkedin_url("") is False


class TestLooksLikeVideoUrl:
    """Video URL detection (Loom, YouTube, etc.)."""

    def test_loom_url(self):
        from formpilot_main import _looks_like_video_url
        assert _looks_like_video_url("https://www.loom.com/share/abc123") is True

    def test_youtube_url(self):
        from formpilot_main import _looks_like_video_url
        assert _looks_like_video_url("https://youtube.com/watch?v=abc") is True

    def test_youtu_be_short(self):
        from formpilot_main import _looks_like_video_url
        assert _looks_like_video_url("https://youtu.be/abc123") is True

    def test_vimeo_url(self):
        from formpilot_main import _looks_like_video_url
        assert _looks_like_video_url("https://vimeo.com/123456") is True

    def test_empty_not_video(self):
        from formpilot_main import _looks_like_video_url
        assert _looks_like_video_url("") is False


class TestLooksLikeEmail:
    """Email validation."""

    def test_valid_email(self):
        from formpilot_main import _looks_like_email
        assert _looks_like_email("dale@prodway.ai") is True

    def test_email_with_plus(self):
        from formpilot_main import _looks_like_email
        assert _looks_like_email("dale+test@prodway.ai") is True

    def test_missing_at_sign(self):
        from formpilot_main import _looks_like_email
        assert _looks_like_email("not-an-email") is False

    def test_empty_not_email(self):
        from formpilot_main import _looks_like_email
        assert _looks_like_email("") is False

    def test_too_long_email(self):
        from formpilot_main import _looks_like_email
        assert _looks_like_email("a" * 321) is False


class TestLooksLikePhone:
    """Phone number validation."""

    def test_us_phone(self):
        from formpilot_main import _looks_like_phone
        assert _looks_like_phone("+1-512-555-0199") is True

    def test_formatted_phone(self):
        from formpilot_main import _looks_like_phone
        assert _looks_like_phone("(512) 555-0199") is True

    def test_plain_digits(self):
        from formpilot_main import _looks_like_phone
        assert _looks_like_phone("5125550199") is True

    def test_too_short(self):
        from formpilot_main import _looks_like_phone
        assert _looks_like_phone("123") is False

    def test_empty_not_phone(self):
        from formpilot_main import _looks_like_phone
        assert _looks_like_phone("") is False

    def test_too_long(self):
        from formpilot_main import _looks_like_phone
        assert _looks_like_phone("1" * 16) is False


class TestValidateMapping:
    """Semantic validation of AI-generated mappings."""

    def test_valid_email_mapping(self):
        from formpilot_main import validate_mapping
        field = {"semanticType": "email"}
        is_valid, err = validate_mapping(field, "test@example.com")
        assert is_valid is True
        assert err is None

    def test_invalid_email_mapping(self):
        from formpilot_main import validate_mapping
        field = {"semanticType": "email"}
        is_valid, err = validate_mapping(field, "not-an-email")
        assert is_valid is False
        assert "email" in err.lower()

    def test_url_in_name_field_rejected(self):
        from formpilot_main import validate_mapping
        field = {"semanticType": "website"}
        is_valid, err = validate_mapping(field, "Dale Yarborough")
        assert is_valid is False

    def test_company_name_in_person_field_rejected(self):
        from formpilot_main import validate_mapping
        field = {"semanticType": "firstName"}
        is_valid, err = validate_mapping(field, "Prodway AI")
        assert is_valid is False
        assert "company" in err.lower()

    def test_short_description_too_short(self):
        from formpilot_main import validate_mapping
        field = {"semanticType": "shortDescription"}
        is_valid, err = validate_mapping(field, "Short")
        assert is_valid is False
        assert "too short" in err

    def test_short_description_valid(self):
        from formpilot_main import validate_mapping
        field = {"semanticType": "shortDescription"}
        is_valid, err = validate_mapping(field, "AI tools for service businesses to scale without scaling headcount.")
        assert is_valid is True

    def test_empty_value_always_valid(self):
        from formpilot_main import validate_mapping
        field = {"semanticType": "email"}
        is_valid, err = validate_mapping(field, "")
        assert is_valid is True

    def test_no_semantic_type_always_valid(self):
        from formpilot_main import validate_mapping
        field = {"label": "Custom Field"}
        is_valid, err = validate_mapping(field, "any value")
        assert is_valid is True

    def test_company_suffix_llc_detected(self):
        from formpilot_main import validate_mapping
        field = {"semanticType": "contactName"}
        is_valid, err = validate_mapping(field, "Acme LLC")
        assert is_valid is False

    def test_company_suffix_inc_detected(self):
        from formpilot_main import validate_mapping
        field = {"semanticType": "lastName"}
        is_valid, err = validate_mapping(field, "Big Corp Inc")
        assert is_valid is False

    def test_valid_phone_mapping(self):
        from formpilot_main import validate_mapping
        field = {"semanticType": "phone"}
        is_valid, err = validate_mapping(field, "+1-512-555-0199")
        assert is_valid is True

    def test_valid_url_mapping(self):
        from formpilot_main import validate_mapping
        field = {"semanticType": "website"}
        is_valid, err = validate_mapping(field, "https://prodway.ai")
        assert is_valid is True

    def test_valid_linkedin_url(self):
        from formpilot_main import validate_mapping
        field = {"semanticType": "linkedinUrl"}
        is_valid, err = validate_mapping(field, "https://linkedin.com/company/prodway")
        assert is_valid is True
