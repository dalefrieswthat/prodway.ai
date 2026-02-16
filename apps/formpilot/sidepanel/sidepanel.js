/**
 * Side panel: same fill flow as popup. Options open in new tab.
 */
(function () {
  const fillBtn = document.getElementById('fill-btn');
  const statusEl = document.getElementById('status');
  const optionsLink = document.getElementById('options-link');

  if (optionsLink) {
    optionsLink.href = chrome.runtime.getURL('options/options.html');
    optionsLink.target = '_blank';
    optionsLink.rel = 'noopener noreferrer';
  }

  function setStatus(text, isSuccess) {
    statusEl.textContent = text;
    statusEl.classList.toggle('success', !!isSuccess);
  }

  function setBusy(busy) {
    fillBtn.disabled = busy;
    fillBtn.querySelector('.btn-text').textContent = busy ? 'Filling…' : 'Fill form';
  }

  async function getActiveTab() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    return tab;
  }

  async function run() {
    const tab = await getActiveTab();
    if (!tab?.id) {
      setStatus('No active tab.', false);
      return;
    }
    if (!tab.url || tab.url.startsWith('chrome://') || tab.url.startsWith('chrome-extension://')) {
      setStatus('Cannot run on this page.', false);
      return;
    }

    setBusy(true);
    setStatus('');

    try {
      const { ok, fields, error } = await chrome.tabs.sendMessage(tab.id, { type: 'FORMPILOT_GET_PAGE_FIELDS' });
      if (!ok || !fields) {
        setStatus(error || 'Could not read form fields.', false);
        setBusy(false);
        return;
      }
      if (fields.length === 0) {
        setStatus('No form fields found. Open the form first (e.g. click Apply), then try Fill form again.', false);
        setBusy(false);
        return;
      }

      const response = await chrome.runtime.sendMessage({
        type: 'FORMPILOT_SUGGEST_MAPPINGS',
        fields,
      });
      const list = (response?.ok && response.mappings) ? response.mappings : [];
      if (list.length === 0) {
        setStatus('No company data to fill. Add data in company data.', false);
        setBusy(false);
        return;
      }

      const fillRes = await chrome.tabs.sendMessage(tab.id, {
        type: 'FORMPILOT_FILL_FIELDS',
        mappings: list,
      });
      if (fillRes?.ok) {
        const validateRes = await chrome.tabs.sendMessage(tab.id, {
          type: 'FORMPILOT_VALIDATE_AFTER_FILL',
          fields,
          mappings: list,
          clearWrong: true,
        }).catch(() => null);
        if (validateRes?.ok && validateRes.fixedCount > 0) {
          setStatus(`Filled ${fillRes.filled} field${fillRes.filled === 1 ? '' : 's'}. Cleared ${validateRes.fixedCount} wrong value(s).`, true);
        } else {
          setStatus(`Filled ${fillRes.filled} field${fillRes.filled === 1 ? '' : 's'}.`, true);
        }
        refreshGlobalStat();
        // Record anonymous usage when user has consented (options → "Share anonymous usage")
        chrome.storage.local.get(['formpilot_usage_consent', 'formpilot_api_base_url'], (o) => {
          if (o.formpilot_usage_consent && fillRes.filled > 0) {
            const base = (o.formpilot_api_base_url || 'https://api.prodway.ai').replace(/\/$/, '');
            fetch(`${base}/prodway/record-fill`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ count: fillRes.filled, consent: true }),
            }).catch(() => {});
          }
        });
      } else {
        setStatus(fillRes?.error || 'Fill failed.', false);
      }
    } catch (e) {
      setStatus('This page may block extensions. Try refreshing.', false);
    } finally {
      setBusy(false);
    }
  }

  async function refreshGlobalStat() {
    const globalEl = document.getElementById('global-stat');
    if (!globalEl) return;
    try {
      const o = await chrome.storage.local.get(['formpilot_api_base_url']);
      const base = (o.formpilot_api_base_url || 'https://api.prodway.ai').replace(/\/$/, '');
      const res = await fetch(`${base}/prodway/stats`);
      const data = await res.json();
      const n = data && typeof data.forms_filled === 'number' ? data.forms_filled : 0;
      globalEl.textContent = n > 0 ? `FormPilot users have filled ${n >= 1000 ? (Math.floor(n / 1000) + 'k+') : (n + '+')} fields total.` : '';
    } catch {
      globalEl.textContent = '';
    }
  }

  fillBtn.addEventListener('click', run);

  refreshGlobalStat();

  getActiveTab().then((tab) => {
    if (tab?.url && !tab.url.startsWith('chrome://') && !tab.url.startsWith('chrome-extension://')) {
      fillBtn.disabled = false;
    }
  });
})();
