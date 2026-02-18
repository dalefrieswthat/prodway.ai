"""
FormPilot API — AI-powered field mapping.
Netflix: single responsibility (suggest mappings only); API key only on backend; stateless.
Deploy to Railway; set ANTHROPIC_API_KEY in Railway app variables.
"""
import os
import json
import logging
import re
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FormPilot API",
    description="AI-powered form field mapping for FormPilot Chrome extension",
    version="1.0.0",
)

# Extension and web origins (Railway app URL for options; chrome-extension:// for popup)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class SuggestMappingsRequest(BaseModel):
    fields: list[dict[str, Any]]
    profile: dict[str, Any] = {}
    context: str | None = None


class SuggestFieldRequest(BaseModel):
    field: dict[str, Any]
    nearby_fields: list[dict[str, Any]] = []
    profile: dict[str, Any] = {}
    context: str | None = None


class ImportFromUrlRequest(BaseModel):
    url: str


class SuggestMappingsResponse(BaseModel):
    mappings: list[dict[str, Any]]


def _looks_like_url(value: str) -> bool:
    """True if value looks like a URL."""
    if not value or len(value) > 2000:
        return False
    v = value.lower().strip()
    if v.startswith("http://") or v.startswith("https://"):
        return True
    # Common URL patterns without protocol
    if re.match(r'^[\w.-]+\.[a-z]{2,}(/|$)', v):
        return True
    return False


def _looks_like_linkedin_url(value: str) -> bool:
    """True if value looks like a LinkedIn URL; False for plain names (avoid wrong fill)."""
    if not value or len(value) > 2000:
        return False
    v = value.lower().strip()
    if "linkedin" in v or v.startswith("http") or ("/" in v and "." in v):
        return True
    # Allow linkedin.com/... without https
    if v.startswith("linkedin.com/") or v.startswith("www.linkedin.com/"):
        return True
    return False


def _looks_like_video_url(value: str) -> bool:
    """True if value looks like a video URL (Loom, YouTube, Vimeo, etc.)."""
    if not value:
        return False
    v = value.lower().strip()
    video_domains = ['loom.com', 'youtube.com', 'youtu.be', 'vimeo.com', 'wistia.com', 'vidyard.com']
    if any(domain in v for domain in video_domains):
        return True
    return _looks_like_url(value)


def _looks_like_email(value: str) -> bool:
    """True if value looks like an email address."""
    if not value or len(value) > 320:
        return False
    return bool(re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', value.strip()))


def _looks_like_phone(value: str) -> bool:
    """True if value looks like a phone number."""
    if not value:
        return False
    # Remove common formatting characters
    digits = re.sub(r'[\s\-\.\(\)\+]', '', value)
    return len(digits) >= 7 and len(digits) <= 15 and digits.isdigit()


# Validation rules by semantic type
VALIDATION_RULES: dict[str, tuple[callable, str]] = {
    'email': (_looks_like_email, 'must be a valid email address'),
    'phone': (_looks_like_phone, 'must be a valid phone number'),
    'website': (_looks_like_url, 'must be a valid URL'),
    'linkedinUrl': (_looks_like_linkedin_url, 'must be a LinkedIn URL'),
    'twitterUrl': (_looks_like_url, 'must be a valid Twitter/X URL'),
    'videoUrl': (_looks_like_video_url, 'must be a video URL (Loom, YouTube, etc.)'),
    'pitchDeckUrl': (_looks_like_url, 'must be a valid URL'),
}

# Length constraints by semantic type
LENGTH_CONSTRAINTS: dict[str, tuple[int, int]] = {
    'shortDescription': (20, 500),  # Elevator pitch: 20-500 chars
    'description': (50, 5000),  # Long description: 50-5000 chars
    'traction': (20, 2000),
    'problemStatement': (20, 2000),
    'solutionStatement': (20, 2000),
    'whyNow': (20, 1000),
    'teamDescription': (20, 3000),
    'uniqueAdvantage': (20, 1000),
    'investorContext': (50, 3000),
    'companyName': (1, 200),
    'contactName': (2, 100),
    'firstName': (1, 50),
    'lastName': (1, 50),
    'city': (1, 100),
    'state': (1, 100),
    'country': (1, 100),
    'zip': (2, 20),
}


def validate_mapping(field: dict, value: str) -> tuple[bool, str | None]:
    """
    Validate a mapping value against its field's semantic type.
    Returns (is_valid, error_message).
    """
    if not value or not value.strip():
        return True, None  # Empty values are OK (just won't be filled)

    semantic_type = field.get('semanticType')
    if not semantic_type:
        return True, None  # No semantic type, can't validate

    value = value.strip()

    # Check validation rules
    if semantic_type in VALIDATION_RULES:
        validator, error_msg = VALIDATION_RULES[semantic_type]
        if not validator(value):
            return False, error_msg

    # Check length constraints
    if semantic_type in LENGTH_CONSTRAINTS:
        min_len, max_len = LENGTH_CONSTRAINTS[semantic_type]
        if len(value) < min_len:
            return False, f'too short (min {min_len} chars)'
        if len(value) > max_len:
            return False, f'too long (max {max_len} chars)'

    # Special case: don't put company name in person name fields
    if semantic_type in ('contactName', 'firstName', 'lastName'):
        # Check if value looks like a company name (ends with Inc, LLC, etc.)
        company_suffixes = ['inc', 'llc', 'ltd', 'corp', 'co', 'company', 'ai', 'io']
        words = value.lower().split()
        if words and words[-1] in company_suffixes:
            return False, 'appears to be a company name, not a person name'

    # Special case: don't put person name in URL fields
    url_types = ['website', 'linkedinUrl', 'twitterUrl', 'videoUrl', 'pitchDeckUrl']
    if semantic_type in url_types:
        # If it doesn't look like a URL at all, reject
        if not _looks_like_url(value) and 'linkedin' not in value.lower():
            return False, 'must be a URL, not plain text'

    return True, None


def build_prompt(fields: list[dict], profile: dict, context: str | None) -> str:
    """Build prompt including optional company context for long-form / YC-style fields."""
    field_summary = []
    prefilled_summary = []
    for i, f in enumerate(fields):
        parts = [f"Index {i}"]
        if f.get("selector"):
            parts.append(f"selector={f['selector']!r}")
        if f.get("label"):
            parts.append(f"label={f['label']!r}")
        if f.get("placeholder"):
            parts.append(f"placeholder={f['placeholder']!r}")
        if f.get("name"):
            parts.append(f"name={f['name']!r}")
        if f.get("semanticType"):
            parts.append(f"semanticType={f['semanticType']!r}")
        current_value = (f.get("value") or "").strip()
        if current_value:
            parts.append(f"currentValue={current_value!r}")
            prefilled_summary.append(f"  Index {i} ({f.get('label') or f.get('name') or f'field {i}'}): {current_value!r}")
        field_summary.append(" ".join(parts))
    fields_text = "\n".join(field_summary)
    profile_text = json.dumps({k: v for k, v in profile.items() if v}, indent=2)
    context_block = ""
    if context and context.strip():
        context_block = f"""
User also provided this company context (use for long-form or custom fields like "Describe your company", "Traction", "Problem/Solution", "YC application answers"; extract the relevant sentence or paragraph for each such field):
---
{context.strip()[:12000]}
---
"""
    prefilled_block = ""
    if prefilled_summary:
        prefilled_block = f"""
Some fields are already filled in on the form. Use these existing values as context to better understand who is filling the form. Do NOT re-output values for fields that already have a currentValue — only fill EMPTY fields:
{chr(10).join(prefilled_summary)}
"""
    return f"""You are a form-fill assistant for founders (YC applications, investor forms, etc.). Given form fields and company data, output the correct value for each field.

Form fields (refer by Index):
{fields_text}

Company profile:
{profile_text}
{context_block}{prefilled_block}

CRITICAL RULES - follow exactly or mappings will be rejected:

1. SKIP fields that already have a currentValue — only fill empty fields.

2. URL FIELDS (website, linkedinUrl, videoUrl, pitchDeckUrl, twitterUrl):
   - ONLY output valid URLs starting with http:// or https:// or domain.com format
   - NEVER put company names or person names in URL fields
   - If you don't have a URL, OMIT the field entirely

3. NAME FIELDS (contactName, firstName, lastName):
   - ONLY output person names, NEVER company names
   - For firstName: first word of contactName
   - For lastName: last word of contactName

4. COMPANY NAME (companyName):
   - ONLY use for fields asking for company/organization name
   - NEVER put company name in description, elevator pitch, or other text fields

5. DESCRIPTION FIELDS (shortDescription, description, elevator pitch):
   - shortDescription/elevator pitch: 1-2 sentences about what the company does (20-500 chars)
   - description: longer explanation from company context (50-5000 chars)
   - These should be SENTENCES, not just the company name

6. VIDEO URL:
   - Must be a Loom, YouTube, Vimeo, or similar video link
   - If no video URL exists, OMIT the field

Output JSON array only: [{{ "index": N, "value": "..." }}]
Only include fields where you have a valid, appropriate value. Omit fields rather than guess wrong.
"""


@app.post("/formpilot/suggest-mappings", response_model=SuggestMappingsResponse)
async def suggest_mappings(body: SuggestMappingsRequest) -> SuggestMappingsResponse:
    """
    Suggest mappings from company profile to form fields using Claude.
    Extension sends fields + profile; we return list of { index, value }.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set; returning empty mappings")
        return SuggestMappingsResponse(mappings=[])

    fields_data = list(body.fields)
    profile = body.profile or {}
    context = (body.context or "").strip() or None

    prompt = build_prompt(fields_data, profile, context)
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text if msg.content else ""
        # Extract JSON array from response (handle markdown code blocks)
        if "```" in text:
            start = text.find("[")
            end = text.rfind("]") + 1
            if start >= 0 and end > start:
                text = text[start:end]
        else:
            start = text.find("[")
            end = text.rfind("]") + 1
            if start >= 0 and end > start:
                text = text[start:end]
        mappings = json.loads(text)
        if not isinstance(mappings, list):
            mappings = []
        # Build index -> field info for validation
        fields_by_index = {i: f for i, f in enumerate(fields_data) if isinstance(f, dict)}

        # Normalize and validate mappings
        out = []
        for m in mappings:
            if not isinstance(m, dict) or "index" not in m:
                continue
            idx = int(m["index"])
            value = str(m.get("value", "")).strip()
            if not value:
                continue
            field = fields_by_index.get(idx)
            if not field:
                continue
            # Apply validation rules
            is_valid, error_msg = validate_mapping(field, value)
            if not is_valid:
                st = field.get("semanticType", "unknown")
                logger.info("Dropping index %s (%s): %s", idx, st, error_msg)
                continue
            out.append({"index": idx, "value": value})

        logger.info("Returning %d valid mappings", len(out))
        return SuggestMappingsResponse(mappings=out)
    except json.JSONDecodeError as e:
        logger.warning("Claude response not valid JSON: %s", e)
        return SuggestMappingsResponse(mappings=[])
    except Exception as e:
        logger.exception("Anthropic call failed")
        raise HTTPException(status_code=502, detail="AI mapping temporarily unavailable")


@app.post("/formpilot/suggest-field")
async def suggest_field(body: SuggestFieldRequest) -> dict:
    """
    Suggest a value for a single field using minimal tokens.
    The sparkle icon sends field context + nearby fields for a targeted suggestion.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return {"value": None, "reasoning": "API key not configured"}

    field = body.field
    nearby = body.nearby_fields or []
    profile = body.profile or {}
    context = (body.context or "").strip() or None

    field_desc = []
    if field.get("label"):
        field_desc.append(f"Label: {field['label']}")
    if field.get("placeholder"):
        field_desc.append(f"Placeholder: {field['placeholder']}")
    if field.get("name"):
        field_desc.append(f"HTML name: {field['name']}")
    if field.get("semanticType"):
        field_desc.append(f"Detected type: {field['semanticType']}")
    if field.get("tagName"):
        field_desc.append(f"Element: {field['tagName']}")

    nearby_desc = ""
    if nearby:
        nearby_lines = []
        for nf in nearby[:8]:
            label = nf.get("label") or nf.get("placeholder") or nf.get("name") or "unknown"
            val = (nf.get("value") or "").strip()
            if val:
                nearby_lines.append(f"  - {label}: \"{val}\"")
            else:
                nearby_lines.append(f"  - {label}: (empty)")
        nearby_desc = f"\nOther fields on the form (for context):\n" + "\n".join(nearby_lines)

    profile_text = json.dumps({k: v for k, v in profile.items() if v}, indent=2) if profile else "{}"

    context_block = ""
    if context:
        context_block = f"\nCompany context:\n{context[:4000]}"

    prompt = f"""Given this specific form field, suggest the best value to fill in based on the company data.

Target field:
{chr(10).join(field_desc)}
{nearby_desc}

Company profile:
{profile_text}
{context_block}

Respond with JSON only: {{"value": "the value to fill", "reasoning": "brief explanation of why this is the right value"}}
If you don't have enough information to confidently fill this field, respond: {{"value": null, "reasoning": "why"}}"""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        text = (msg.content[0].text if msg.content else "").strip()
        if "```" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                text = text[start:end]
        data = json.loads(text)
        value = data.get("value")
        reasoning = data.get("reasoning", "")

        if value:
            is_valid, error_msg = validate_mapping(field, str(value))
            if not is_valid:
                return {"value": None, "reasoning": error_msg}

        return {"value": value, "reasoning": reasoning}
    except (json.JSONDecodeError, KeyError):
        return {"value": None, "reasoning": "Could not parse AI response"}
    except Exception as e:
        logger.exception("suggest-field failed")
        return {"value": None, "reasoning": "AI temporarily unavailable"}


def _strip_html(html: str) -> str:
    """Crude strip of HTML tags for LLM."""
    text = re.sub(r"<script[^>]*>[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    text = re.sub(r"<style[^>]*>[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()[:15000]


@app.post("/formpilot/import-from-url")
async def import_from_url(body: ImportFromUrlRequest) -> dict:
    """
    Fetch URL (e.g. LinkedIn company page), extract text, use Claude to extract
    structured profile + company context. Returns { profile, context } for extension.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not set")

    url = (body.url or "").strip()
    if not url or not url.startswith("http"):
        raise HTTPException(status_code=400, detail="Invalid URL")

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            resp = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; FormPilot/1.0)"},
            )
            resp.raise_for_status()
            raw = resp.text
    except Exception as e:
        logger.warning("Fetch failed for %s: %s", url, e)
        raise HTTPException(status_code=422, detail="Could not fetch URL")

    text = _strip_html(raw)
    if not text:
        raise HTTPException(status_code=422, detail="No text content extracted")

    prompt = f"""The following text was extracted from a web page (e.g. LinkedIn, company site). Extract structured company/contact info and a short company context.

Page text:
---
{text[:12000]}
---

Output a JSON object with two keys:
1) "profile": object with keys only if you found a value: companyName, contactName, email, phone, website, address, city, state, zip, country, linkedinUrl, description (one short sentence).
2) "context": string with 1-3 paragraphs summarizing the company (what they do, traction, problem/solution) suitable for pasting into "Company context" to fill long-form form fields.

Respond with only the JSON object, no markdown."""

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        reply = (msg.content[0].text if msg.content else "").strip()
        if "```" in reply:
            start = reply.find("{")
            end = reply.rfind("}") + 1
            if start >= 0 and end > start:
                reply = reply[start:end]
        data = json.loads(reply)
        profile = data.get("profile") or {}
        context = data.get("context") or ""
        return {"profile": profile, "context": context}
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("Import parse failed: %s", e)
        raise HTTPException(status_code=502, detail="Could not extract structured data from page")
    except Exception as e:
        logger.exception("Import failed")
        raise HTTPException(status_code=502, detail="Import failed")


@app.get("/formpilot/health")
async def health() -> dict:
    """Health check for Railway."""
    return {"status": "ok", "service": "formpilot-api"}


# --- Prodway usage stats (forms filled, SOWs sent) for landing page & moat ---

class RecordFillRequest(BaseModel):
    count: int = 1
    consent: bool = False


class RecordSowRequest(BaseModel):
    consent: bool = False


@app.post("/prodway/record-fill")
async def record_fill(body: RecordFillRequest) -> dict:
    """
    Record form fills (with consent). Called by FormPilot after successful fill.
    Used for landing-page stats and "we know what scaling teams need."
    """
    if not body.consent or body.count <= 0:
        return {"ok": True, "recorded": 0}
    try:
        from usage_db import record_forms_filled
        record_forms_filled(body.count)
        return {"ok": True, "recorded": body.count}
    except Exception as e:
        logger.warning("record_fill failed: %s", e)
        return {"ok": False, "recorded": 0}


@app.post("/prodway/record-sow")
async def record_sow(body: RecordSowRequest) -> dict:
    """
    Record SOW sent (with consent). Called by SowFlow when an SOW is sent (e.g. DocuSign).
    """
    if not body.consent:
        return {"ok": True, "recorded": 0}
    try:
        from usage_db import record_sows_sent
        record_sows_sent(1)
        return {"ok": True, "recorded": 1}
    except Exception as e:
        logger.warning("record_sow failed: %s", e)
        return {"ok": False, "recorded": 0}


@app.get("/prodway/stats")
async def get_stats() -> dict:
    """
    Public stats for landing page: forms_filled, sows_sent.
    No auth; safe aggregate counts only.
    """
    try:
        from usage_db import get_stats
        forms_filled, sows_sent = get_stats()
        return {"forms_filled": forms_filled, "sows_sent": sows_sent}
    except Exception as e:
        logger.warning("get_stats failed: %s", e)
        return {"forms_filled": 0, "sows_sent": 0}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
