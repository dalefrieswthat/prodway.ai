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


class ImportFromUrlRequest(BaseModel):
    url: str


class SuggestMappingsResponse(BaseModel):
    mappings: list[dict[str, Any]]


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


def build_prompt(fields: list[dict], profile: dict, context: str | None) -> str:
    """Build prompt including optional company context for long-form / YC-style fields."""
    field_summary = []
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
    return f"""You are a form-fill assistant for founders and teams (e.g. YC applications, investor forms). Given form fields, a structured profile, and optional company context, output which value should fill each field.

Form fields (use Index to refer to them):
{fields_text}

Structured profile (prefer for exact matches like email, company name):
{profile_text}
{context_block}

Respond with a JSON array only. Each element: {{ "index": <field index number>, "value": "<value from profile or context or empty string>" }}.
- For short fields (email, name, company) use the profile.
- For "first name" / "last name": use the first word of contactName for first name, last word for last name. Do not put a person's name in any other field type.
- For LinkedIn / linkedin URL: use ONLY a valid URL (e.g. linkedin.com/... or https://linkedin.com/...). Never put a person's name in the LinkedIn field. If you only have a name and no URL, leave the LinkedIn field empty (omit it from the array).
- For long-form or custom fields (description, traction, problem, solution) use the relevant part of the company context.
Include only fields that should be filled (value non-empty). Order does not matter.
Example: [{{ "index": 0, "value": "Acme Inc." }}, {{ "index": 2, "value": "We help startups scale infrastructure without hiring." }}]
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
        # Normalize and validate: ensure value matches field type (e.g. no name in LinkedIn URL)
        out = []
        for m in mappings:
            if not isinstance(m, dict) or "index" not in m:
                continue
            idx = int(m["index"])
            value = str(m.get("value", "")).strip()
            field = fields_by_index.get(idx)
            if field and field.get("semanticType") == "linkedinUrl" and value:
                # Reject non-URLs in LinkedIn field (e.g. person name) to avoid wrong fill
                if not _looks_like_linkedin_url(value):
                    logger.info("Dropping mapping index %s: LinkedIn field got non-URL value", idx)
                    continue
            out.append({"index": idx, "value": value})
        return SuggestMappingsResponse(mappings=out)
    except json.JSONDecodeError as e:
        logger.warning("Claude response not valid JSON: %s", e)
        return SuggestMappingsResponse(mappings=[])
    except Exception as e:
        logger.exception("Anthropic call failed")
        raise HTTPException(status_code=502, detail="AI mapping temporarily unavailable")


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
