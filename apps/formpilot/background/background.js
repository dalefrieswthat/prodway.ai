/**
 * FormPilot background — on-demand AI suggestions only.
 * Calls the API exclusively when the user clicks a sparkle icon (suggest-field).
 * No auto-fire batch suggestions on page load.
 */
const DEFAULT_API_BASE = 'https://api.prodway.ai';
const STORAGE_KEYS = {
  COMPANY_PROFILE: 'formpilot_company_profile',
  COMPANY_CONTEXT: 'formpilot_company_context',
  API_BASE_URL: 'formpilot_api_base_url',
};

async function getStored(key, defaultValue) {
  const o = await chrome.storage.local.get(key);
  return o[key] ?? defaultValue;
}

async function getCompanyProfile() {
  const raw = await getStored(STORAGE_KEYS.COMPANY_PROFILE, null);
  if (!raw) return null;
  try {
    return typeof raw === 'string' ? JSON.parse(raw) : raw;
  } catch {
    return null;
  }
}

async function getCompanyContext() {
  const raw = await getStored(STORAGE_KEYS.COMPANY_CONTEXT, '');
  return typeof raw === 'string' ? raw : '';
}

async function getApiBaseUrl() {
  return (await getStored(STORAGE_KEYS.API_BASE_URL, DEFAULT_API_BASE)).replace(/\/$/, '');
}

chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});

async function suggestSingleField(field, nearbyFields) {
  const profile = await getCompanyProfile();
  const context = await getCompanyContext();
  const base = await getApiBaseUrl();
  const url = `${base}/formpilot/suggest-field`;
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        field,
        nearby_fields: nearbyFields || [],
        profile: profile || {},
        context: context || '',
      }),
    });
    if (!res.ok) return { value: null, reasoning: 'API error' };
    return await res.json();
  } catch {
    return { value: null, reasoning: 'Network error' };
  }
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'FORMPILOT_SUGGEST_FIELD') {
    (async () => {
      const result = await suggestSingleField(msg.field, msg.nearbyFields);
      sendResponse({ ok: true, value: result.value, reasoning: result.reasoning });
    })();
    return true;
  }

  return false;
});
