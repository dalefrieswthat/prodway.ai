# FormPilot — Chrome Extension

Auto-fill forms with your company data. YC applications, vendor forms, RFPs—done in seconds.

## Architecture (Netflix-style)

- **Content script**: Detects form fields only; executes fill commands. No API calls, minimal surface.
- **Background (service worker)**: Orchestration only. Calls backend for AI mappings; falls back to heuristic if backend is down (circuit breaker).
- **Popup**: Single CTA “Fill form”; gets fields from tab → mappings from background → sends fill to content script.
- **Options**: Company profile (chrome.storage.local). No backend dependency.
- **Backend (FormPilot API)**: Stateless; uses Anthropic to suggest field→profile mappings. Deploy to Railway with `ANTHROPIC_API_KEY`.

## Design (Airbnb quality)

- Design tokens in popup/options CSS (colors, spacing, radius).
- Clear hierarchy, 44px min touch targets, focus states.
- No clutter; one primary action per screen.

## Setup

### 1. Load the extension

1. Open `chrome://extensions`
2. Enable **Developer mode**
3. **Load unpacked** → select `apps/formpilot`

### 2. Company data

1. Click the extension icon → **Edit company data**
2. Fill in company name, contact, email, etc. and **Save**

### 3. Backend (optional but recommended)

- Deploy `apps/formpilot-api` to Railway.
- Set **ANTHROPIC_API_KEY** in Railway app variables.
- In extension options (or via storage), set **API base URL** to your Railway URL (e.g. `https://your-app.up.railway.app`) if different from `https://api.prodway.ai`.

Default API base URL is `https://api.prodway.ai`. To use a separate FormPilot API on Railway, set `formpilot_api_base_url` in chrome.storage (e.g. from a future options field).

### 4. Use

- Open any page with a form.
- Click the FormPilot icon → **Fill form**.
- Fields are matched from your profile (AI if backend is set, else heuristic).

### 5. WebMCP (optional)

When Chrome’s WebMCP is available (Chrome 146+ with flag, or future release), FormPilot registers a tool **`formpilot_validate_fill`** so in-browser agents (or DevTools MCP) can run the same DOM-snapshot validation. After a fill, an agent can call the tool with `fields` and `mappings` to validate and optionally clear wrong values (e.g. non-URL in LinkedIn). No screenshot or vision—validation stays DOM-based.

## Project layout

```
apps/formpilot/
  manifest.json       # MV3
  popup/              # Popup UI
  content/            # Content script + form detector
  injected/           # WebMCP bridge (page context)
  background/         # Service worker
  options/            # Company data form
  lib/                # form-detector.js, constants
  icons/
apps/formpilot-api/   # FastAPI backend (Railway)
  main.py
  requirements.txt
```

## Icons

Icons are copied from the web app. Replace `icons/icon16.png`, `icon48.png`, `icon128.png` with FormPilot-specific assets if desired.
