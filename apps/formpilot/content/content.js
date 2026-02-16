/**
 * FormPilot content script — WebMCP-style: fill by stable selector when available, else by index.
 * After fill, DOM snapshot validation ensures values are in the right spots (no vision/screenshot).
 */
(function () {
  const SCRIPT_TAG = 'formpilot-content';
  const SELECTORS = 'input:not([type="hidden"]):not([type="submit"]):not([type="button"]), textarea, select';

  if (document.querySelector(`[data-${SCRIPT_TAG}]`)) return;
  document.documentElement.setAttribute(`data-${SCRIPT_TAG}`, 'true');

  function getFields() {
    if (typeof FormPilotDetector === 'undefined') return [];
    return FormPilotDetector.detectFields();
  }

  function getElementForMapping(m, fields) {
    if (m.selector) {
      try {
        const el = document.querySelector(m.selector);
        if (el) return el;
      } catch (_) {}
    }
    if (typeof m.index === 'number' && fields && fields[m.index]) {
      const f = fields[m.index];
      if (f.selector) {
        try {
          const el = document.querySelector(f.selector);
          if (el) return el;
        } catch (_) {}
      }
      const elements = document.querySelectorAll(SELECTORS);
      return elements[m.index] || null;
    }
    return null;
  }

  /** Fill fields using selector (WebMCP-style) or index fallback. */
  function fillFields(mappings) {
    let filled = 0;
    const list = mappings || [];
    for (let i = 0; i < list.length; i++) {
      const m = list[i];
      const value = m.value;
      if (value == null || value === '') continue;
      const el = getElementForMapping(m, null);
      if (el) {
        el.value = value;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        filled++;
      }
    }
    return filled;
  }

  function looksLikeLinkedInUrl(value) {
    if (!value || value.length > 2000) return false;
    const v = value.toLowerCase().trim();
    if (v.includes('linkedin') || v.startsWith('http') || (v.includes('/') && v.includes('.'))) return true;
    if (v.startsWith('linkedin.com/') || v.startsWith('www.linkedin.com/')) return true;
    return false;
  }

  /**
   * DOM snapshot after fill: read back values and validate.
   * - Check value matches what we set.
   * - For semanticType linkedinUrl, value must look like a URL (else clear and report).
   * Returns { ok, errors: [{ index, label, reason, cleared }], fixedCount }.
   */
  function validateAfterFill(fields, mappings, clearWrong) {
    const errors = [];
    let fixedCount = 0;
    const byIndex = new Map((mappings || []).map((m) => [m.index, m]));
    (fields || []).forEach((f) => {
      const m = byIndex.get(f.index);
      if (!m || m.value == null || m.value === '') return;
      const el = getElementForMapping(m, fields);
      if (!el) return;
      const actual = (el.value || '').trim();
      const expected = String(m.value || '').trim();
      if (actual !== expected) {
        errors.push({ index: f.index, label: f.label || f.placeholder || 'Field ' + f.index, reason: 'value_mismatch', cleared: false });
        if (clearWrong) {
          el.value = '';
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
          errors[errors.length - 1].cleared = true;
          fixedCount++;
        }
        return;
      }
      if (f.semanticType === 'linkedinUrl' && actual && !looksLikeLinkedInUrl(actual)) {
        errors.push({ index: f.index, label: f.label || f.placeholder || 'LinkedIn', reason: 'linkedin_not_url', cleared: false });
        if (clearWrong) {
          el.value = '';
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
          errors[errors.length - 1].cleared = true;
          fixedCount++;
        }
      }
    });
    return { ok: errors.length === 0, errors, fixedCount };
  }

  const WEBMCP_PREFIX = 'FORMPILOT_WEBMCP_';
  window.addEventListener('message', (e) => {
    if (e.source !== window || e.data?.type !== WEBMCP_PREFIX + 'RUN') return;
    const { requestId, fields = [], mappings = [], clearWrong = true } = e.data;
    try {
      const result = validateAfterFill(fields, mappings, clearWrong);
      window.postMessage({ type: WEBMCP_PREFIX + 'RESULT', requestId, result }, '*');
    } catch (err) {
      window.postMessage({ type: WEBMCP_PREFIX + 'RESULT', requestId, result: { ok: false, error: String(err.message) } }, '*');
    }
  });

  function injectWebMCPBridge() {
    if (document.documentElement.getAttribute('data-formpilot-webmcp-injected')) return;
    document.documentElement.setAttribute('data-formpilot-webmcp-injected', 'true');
    const script = document.createElement('script');
    script.src = chrome.runtime.getURL('injected/webmcp-validate.js');
    script.onload = () => script.remove();
    (document.head || document.documentElement).appendChild(script);
  }
  injectWebMCPBridge();

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg.type === 'FORMPILOT_GET_PAGE_FIELDS') {
      try {
        sendResponse({ ok: true, fields: getFields() });
      } catch (e) {
        sendResponse({ ok: false, error: e.message });
      }
    } else if (msg.type === 'FORMPILOT_FILL_FIELDS') {
      try {
        const filled = fillFields(msg.mappings || []);
        sendResponse({ ok: true, filled });
      } catch (e) {
        sendResponse({ ok: false, error: e.message });
      }
    } else if (msg.type === 'FORMPILOT_VALIDATE_AFTER_FILL') {
      try {
        const { fields = [], mappings = [], clearWrong = true } = msg;
        const result = validateAfterFill(fields, mappings, clearWrong);
        sendResponse({ ok: true, ...result });
      } catch (e) {
        sendResponse({ ok: false, error: e.message });
      }
    } else {
      sendResponse({ ok: false, error: 'Unknown message type' });
    }
    return true;
  });
})();
