/**
 * FormPilot background — orchestration; sends profile + context to backend; enriches mappings with selectors (WebMCP-style).
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

async function suggestMappings(fields, profile, context) {
  const base = await getApiBaseUrl();
  const url = `${base}/formpilot/suggest-mappings`;
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        fields,
        profile: profile || {},
        context: context || '',
      }),
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data.mappings || null;
  } catch {
    return null;
  }
}

function heuristicMappings(fields, profile) {
  if (!profile || typeof profile !== 'object') return [];
  const map = {
    email: 'email',
    phone: 'phone',
    companyName: 'companyName',
    contactName: 'contactName',
    website: 'website',
    address: 'address',
    city: 'city',
    state: 'state',
    zip: 'zip',
    country: 'country',
    linkedinUrl: 'linkedinUrl',
    description: 'description',
  };
  const byIndex = new Map();
  fields.forEach((f) => {
    if (f.semanticType && map[f.semanticType]) {
      const value = profile[map[f.semanticType]] || '';
      if (value) byIndex.set(f.index, { index: f.index, selector: f.selector, value });
    }
  });
  return Array.from(byIndex.values());
}

/** Enrich backend mappings with selector from snapshot (WebMCP-style placement). */
function enrichMappingsWithSelectors(mappings, fields) {
  const byIndex = new Map();
  (fields || []).forEach((f) => byIndex.set(f.index, f.selector));
  return (mappings || []).map((m) => ({
    index: m.index,
    selector: m.selector != null ? m.selector : byIndex.get(m.index) || null,
    value: m.value,
  }));
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type !== 'FORMPILOT_SUGGEST_MAPPINGS') return false;
  (async () => {
    const profile = await getCompanyProfile();
    const context = await getCompanyContext();
    const fields = msg.fields || [];
    let mappings = await suggestMappings(fields, profile, context);
    if (!mappings || mappings.length === 0) {
      mappings = heuristicMappings(fields, profile);
    }
    const enriched = enrichMappingsWithSelectors(mappings, fields);
    sendResponse({ ok: true, mappings: enriched });
  })();
  return true;
});
