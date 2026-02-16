/**
 * Options: profile, company context (paste + file), import from URL.
 */
(function () {
  const FORM = document.getElementById('profile-form');
  const SAVE_STATUS = document.getElementById('save-status');
  const CONTEXT_INPUT = document.getElementById('companyContext');
  const CONTEXT_FILE = document.getElementById('contextFile');
  const IMPORT_URL_INPUT = document.getElementById('importUrl');
  const IMPORT_URL_BTN = document.getElementById('import-url-btn');
  const STORAGE_KEYS = {
    profile: 'formpilot_company_profile',
    context: 'formpilot_company_context',
    apiBaseUrl: 'formpilot_api_base_url',
    usageConsent: 'formpilot_usage_consent',
  };
  const DEFAULT_API_BASE = 'https://api.prodway.ai';
  const FIELDS = [
    'companyName', 'contactName', 'email', 'phone', 'website',
    'address', 'city', 'state', 'zip', 'country', 'linkedinUrl', 'description',
  ];

  function getProfile() {
    const o = {};
    FIELDS.forEach((name) => {
      const el = document.getElementById(name);
      if (el) o[name] = (el.value || '').trim();
    });
    return o;
  }

  function getCompanyContext() {
    return CONTEXT_INPUT ? (CONTEXT_INPUT.value || '').trim() : '';
  }

  function getApiBaseUrl() {
    const el = document.getElementById('apiBaseUrl');
    return (el && el.value.trim()) || '';
  }

  function setProfile(profile) {
    if (!profile || typeof profile !== 'object') return;
    FIELDS.forEach((name) => {
      const el = document.getElementById(name);
      if (el && profile[name] != null) el.value = profile[name];
    });
  }

  function setCompanyContext(text) {
    if (CONTEXT_INPUT) CONTEXT_INPUT.value = text || '';
  }

  function setApiBaseUrl(url) {
    const el = document.getElementById('apiBaseUrl');
    if (el) el.value = url || DEFAULT_API_BASE;
  }

  function showStatus(text, saved) {
    SAVE_STATUS.textContent = text;
    SAVE_STATUS.classList.toggle('saved', !!saved);
  }

  if (CONTEXT_FILE) CONTEXT_FILE.addEventListener('change', function () {
    const file = this.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function () {
      const current = getCompanyContext();
      const added = typeof reader.result === 'string' ? reader.result : '';
      setCompanyContext(current ? current + '\n\n' + added : added);
    };
    reader.readAsText(file);
    this.value = '';
  });

  if (IMPORT_URL_BTN) IMPORT_URL_BTN.addEventListener('click', async function () {
    const url = (IMPORT_URL_INPUT && IMPORT_URL_INPUT.value.trim()) || '';
    if (!url) {
      showStatus('Enter a URL first.', false);
      return;
    }
    IMPORT_URL_BTN.disabled = true;
    showStatus('Fetching…', false);
    try {
      const base = (await new Promise((r) => chrome.storage.local.get(STORAGE_KEYS.apiBaseUrl, (o) => r(o[STORAGE_KEYS.apiBaseUrl] || DEFAULT_API_BASE)))).replace(/\/$/, '');
      const res = await fetch(`${base}/formpilot/import-from-url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      if (!res.ok) {
        const err = await res.text();
        showStatus('Import failed: ' + (err || res.status), false);
        return;
      }
      const data = await res.json();
      if (data.profile) setProfile(data.profile);
      if (data.context) setCompanyContext(data.context);
      showStatus('Imported. Save to store.', true);
    } catch (e) {
      showStatus('Import failed: ' + e.message, false);
    } finally {
      IMPORT_URL_BTN.disabled = false;
    }
  });

  if (!FORM) return;
  function getUsageConsent() {
    const el = document.getElementById('usageConsent');
    return el ? el.checked : false;
  }

  function setUsageConsent(checked) {
    const el = document.getElementById('usageConsent');
    if (el) el.checked = !!checked;
  }

  FORM.addEventListener('submit', async (e) => {
    e.preventDefault();
    const profile = getProfile();
    const context = getCompanyContext();
    const apiBaseUrl = getApiBaseUrl();
    const usageConsent = getUsageConsent();
    await chrome.storage.local.set({
      [STORAGE_KEYS.profile]: profile,
      [STORAGE_KEYS.context]: context,
      [STORAGE_KEYS.apiBaseUrl]: apiBaseUrl || DEFAULT_API_BASE,
      [STORAGE_KEYS.usageConsent]: usageConsent,
    });
    showStatus('Saved.', true);
    setTimeout(() => showStatus('', false), 2000);
  });

  chrome.storage.local.get([STORAGE_KEYS.profile, STORAGE_KEYS.context, STORAGE_KEYS.apiBaseUrl, STORAGE_KEYS.usageConsent], (o) => {
    if (o[STORAGE_KEYS.profile]) setProfile(o[STORAGE_KEYS.profile]);
    setCompanyContext(o[STORAGE_KEYS.context] || '');
    setApiBaseUrl(o[STORAGE_KEYS.apiBaseUrl] || DEFAULT_API_BASE);
    setUsageConsent(o[STORAGE_KEYS.usageConsent] === true);
  });
})();
