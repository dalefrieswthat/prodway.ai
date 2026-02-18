/**
 * FormPilot background — orchestration; sends profile + context to backend; enriches mappings with selectors (WebMCP-style).
 * Includes suggestion caching with TTL and invalidation on profile/context changes.
 */
const DEFAULT_API_BASE = 'https://api.prodway.ai';
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minute cache TTL
const STORAGE_KEYS = {
  COMPANY_PROFILE: 'formpilot_company_profile',
  COMPANY_CONTEXT: 'formpilot_company_context',
  API_BASE_URL: 'formpilot_api_base_url',
  SUGGESTION_CACHE: 'formpilot_suggestion_cache',
  CACHE_TIMESTAMP: 'formpilot_cache_timestamp',
};

// In-memory cache for suggestions (survives during browser session)
let suggestionCache = {
  data: null,
  timestamp: 0,
  profileHash: null,
  contextHash: null,
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

function simpleHash(str) {
  if (!str) return '';
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return Math.abs(hash).toString(36);
}

async function getCacheKey(fields) {
  // Create a fingerprint of fields (selectors, semanticTypes)
  const fingerprint = (fields || [])
    .map((f) => `${f.selector}|${f.semanticType}`)
    .join(';');
  return simpleHash(fingerprint);
}

function isCacheValid(profileHash, contextHash) {
  if (!suggestionCache.data) return false;
  if (Date.now() - suggestionCache.timestamp > CACHE_TTL_MS) return false;
  if (suggestionCache.profileHash !== profileHash) return false;
  if (suggestionCache.contextHash !== contextHash) return false;
  return true;
}

function setCacheEntry(data, profileHash, contextHash) {
  suggestionCache.data = data;
  suggestionCache.timestamp = Date.now();
  suggestionCache.profileHash = profileHash;
  suggestionCache.contextHash = contextHash;
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

function looksLikeUrl(v) {
  if (!v) return false;
  v = v.toLowerCase().trim();
  return v.startsWith('http') || v.includes('://') || /^[\w.-]+\.[a-z]{2,}(\/|$)/.test(v);
}

function heuristicMappings(fields, profile) {
  if (!profile || typeof profile !== 'object') return [];

  // Split contactName into first/last for name fields
  const nameParts = (profile.contactName || '').trim().split(/\s+/);
  const firstName = nameParts[0] || '';
  const lastName = nameParts.length > 1 ? nameParts[nameParts.length - 1] : '';

  const byIndex = new Map();
  fields.forEach((f) => {
    if (!f.semanticType) return;
    let value = '';

    switch (f.semanticType) {
      // Direct profile mappings
      case 'email': value = profile.email || ''; break;
      case 'phone': value = profile.phone || ''; break;
      case 'companyName': value = profile.companyName || ''; break;
      case 'address': value = profile.address || ''; break;
      case 'city': value = profile.city || ''; break;
      case 'state': value = profile.state || ''; break;
      case 'zip': value = profile.zip || ''; break;
      case 'country': value = profile.country || ''; break;

      // Name splitting
      case 'firstName': value = firstName; break;
      case 'lastName': value = lastName; break;
      case 'contactName': value = profile.contactName || ''; break;

      // URL fields — ONLY fill if value looks like a URL
      case 'website':
        value = profile.website || '';
        if (value && !looksLikeUrl(value)) value = '';
        break;
      case 'linkedinUrl':
        value = profile.linkedinUrl || '';
        if (value && !looksLikeUrl(value) && !value.toLowerCase().includes('linkedin')) value = '';
        break;
      case 'twitterUrl':
        value = profile.twitterUrl || '';
        if (value && !looksLikeUrl(value)) value = '';
        break;
      case 'videoUrl':
      case 'pitchDeckUrl':
        // Never fill from heuristics — these need real URLs
        break;

      // Text fields — only fill description, skip others (need AI context)
      case 'description':
        value = profile.description || '';
        break;
      case 'shortDescription':
        value = profile.description || '';
        break;

      // Skip all other types in heuristics (traction, problem, team, etc.)
      default:
        break;
    }

    if (value) {
      byIndex.set(f.index, { index: f.index, selector: f.selector, value });
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

chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});

// Invalidate cache when profile or context changes
chrome.storage.onChanged.addListener((changes) => {
  if (changes[STORAGE_KEYS.COMPANY_PROFILE] || changes[STORAGE_KEYS.COMPANY_CONTEXT]) {
    suggestionCache.data = null; // Clear in-memory cache
  }
});

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

  if (msg.type !== 'FORMPILOT_SUGGEST_MAPPINGS') return false;
  (async () => {
    const profile = await getCompanyProfile();
    const context = await getCompanyContext();
    const fields = msg.fields || [];

    // Create hash for cache validation
    const profileHash = simpleHash(JSON.stringify(profile || {}));
    const contextHash = simpleHash(context || '');

    // Check cache
    if (isCacheValid(profileHash, contextHash)) {
      const enriched = enrichMappingsWithSelectors(suggestionCache.data || [], fields);
      sendResponse({ ok: true, mappings: enriched });
      return;
    }

    // Not cached, fetch from API
    let mappings = await suggestMappings(fields, profile, context);
    if (!mappings || mappings.length === 0) {
      mappings = heuristicMappings(fields, profile);
    }

    // Cache the result
    setCacheEntry(mappings, profileHash, contextHash);

    const enriched = enrichMappingsWithSelectors(mappings, fields);
    sendResponse({ ok: true, mappings: enriched });
  })();
  return true;
});
