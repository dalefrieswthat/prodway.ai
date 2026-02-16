/**
 * FormPilot content script — WebMCP-style: fill by stable selector when available, else by index.
 */
(function () {
  const SCRIPT_TAG = 'formpilot-content';

  if (document.querySelector(`[data-${SCRIPT_TAG}]`)) return;
  document.documentElement.setAttribute(`data-${SCRIPT_TAG}`, 'true');

  function getFields() {
    if (typeof FormPilotDetector === 'undefined') return [];
    return FormPilotDetector.detectFields();
  }

  /** Fill fields using selector (WebMCP-style) or index fallback. */
  function fillFields(mappings) {
    let filled = 0;
    const list = mappings || [];
    for (let i = 0; i < list.length; i++) {
      const m = list[i];
      const value = m.value;
      if (value == null || value === '') continue;
      let el = null;
      if (m.selector) {
        try {
          el = document.querySelector(m.selector);
        } catch (_) {}
      }
      if (!el && typeof m.index === 'number') {
        const SELECTORS = 'input:not([type="hidden"]):not([type="submit"]):not([type="button"]), textarea, select';
        const elements = document.querySelectorAll(SELECTORS);
        el = elements[m.index] || null;
      }
      if (el) {
        el.value = value;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        filled++;
      }
    }
    return filled;
  }

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
    } else {
      sendResponse({ ok: false, error: 'Unknown message type' });
    }
    return true;
  });
})();
