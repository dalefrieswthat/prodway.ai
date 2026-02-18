/**
 * FormPilot content script — on-demand AI suggestions via sparkle icons.
 * Detects form fields, places sparkle buttons, and calls AI only when clicked.
 * Zero API calls on page load.
 */
(function () {
  var SCRIPT_TAG = 'formpilot-content';
  var SELECTORS = 'input:not([type="hidden"]):not([type="submit"]):not([type="button"]), textarea, select';

  if (document.querySelector('[data-' + SCRIPT_TAG + ']')) return;
  document.documentElement.setAttribute('data-' + SCRIPT_TAG, 'true');

  // State
  var cachedFields = null;
  var mutationObserver = null;
  var sparkleButtons = new Map(); // selector -> sparkle button element
  var activeTooltip = null;

  function getFields() {
    if (typeof FormPilotDetector === 'undefined') return [];
    cachedFields = FormPilotDetector.detectFields();
    return cachedFields;
  }

  function getElementForMapping(m, fields) {
    if (m.selector) {
      try {
        var el = document.querySelector(m.selector);
        if (el) return el;
      } catch (_) {}
    }
    if (typeof m.index === 'number' && fields && fields[m.index]) {
      var f = fields[m.index];
      if (f.selector) {
        try {
          var el2 = document.querySelector(f.selector);
          if (el2) return el2;
        } catch (_) {}
      }
      var elements = document.querySelectorAll(SELECTORS);
      return elements[m.index] || null;
    }
    return null;
  }

  /** Fill fields using selector (WebMCP-style) or index fallback. */
  function fillFields(mappings) {
    var filled = 0;
    var list = mappings || [];
    for (var i = 0; i < list.length; i++) {
      var m = list[i];
      var value = m.value;
      if (value == null || value === '') continue;
      var el = getElementForMapping(m, null);
      if (el) {
        el.value = value;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        filled++;
      }
    }
    return filled;
  }

  function looksLikeUrl(value) {
    if (!value || value.length > 2000) return false;
    var v = value.toLowerCase().trim();
    return v.startsWith('http') || v.includes('://') || /^[\w.-]+\.[a-z]{2,}(\/|$)/.test(v);
  }

  function looksLikeLinkedInUrl(value) {
    if (!value || value.length > 2000) return false;
    var v = value.toLowerCase().trim();
    if (v.includes('linkedin') || v.startsWith('http') || (v.includes('/') && v.includes('.'))) return true;
    if (v.startsWith('linkedin.com/') || v.startsWith('www.linkedin.com/')) return true;
    return false;
  }

  /**
   * DOM snapshot after fill: read back values and validate.
   */
  function validateAfterFill(fields, mappings, clearWrong) {
    var errors = [];
    var fixedCount = 0;
    var byIndex = new Map((mappings || []).map(function(m) { return [m.index, m]; }));

    (fields || []).forEach(function(f) {
      var m = byIndex.get(f.index);
      if (!m || m.value == null || m.value === '') return;
      var el = getElementForMapping(m, fields);
      if (!el) return;
      var actual = (el.value || '').trim();
      var expected = String(m.value || '').trim();

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

      var urlTypes = ['linkedinUrl', 'website', 'videoUrl', 'pitchDeckUrl', 'twitterUrl'];
      if (urlTypes.indexOf(f.semanticType) !== -1 && actual && !looksLikeUrl(actual)) {
        errors.push({ index: f.index, label: f.label || f.placeholder || 'URL', reason: 'not_url', cleared: false });
        if (clearWrong) {
          el.value = '';
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
          errors[errors.length - 1].cleared = true;
          fixedCount++;
        }
      }
    });

    return { ok: errors.length === 0, errors: errors, fixedCount: fixedCount };
  }

  /**
   * Dismiss any open tooltip.
   */
  function dismissTooltip() {
    if (activeTooltip) {
      activeTooltip.remove();
      activeTooltip = null;
    }
  }

  /**
   * Show a tooltip with the AI suggestion near the sparkle button.
   */
  function showTooltip(btn, field, value, reasoning) {
    dismissTooltip();

    var tip = document.createElement('div');
    tip.className = 'fp-tooltip';

    if (!value) {
      tip.innerHTML = '<div class="fp-tooltip-empty">' + (reasoning || 'No suggestion available for this field.') + '</div>';
      var closeBtn = document.createElement('button');
      closeBtn.className = 'fp-tooltip-btn fp-tooltip-dismiss';
      closeBtn.textContent = 'OK';
      closeBtn.onclick = function() { dismissTooltip(); };
      var actions = document.createElement('div');
      actions.className = 'fp-tooltip-actions';
      actions.appendChild(closeBtn);
      tip.appendChild(actions);
    } else {
      var valDiv = document.createElement('div');
      valDiv.className = 'fp-tooltip-value';
      valDiv.textContent = value.length > 200 ? value.substring(0, 200) + '…' : value;
      tip.appendChild(valDiv);

      if (reasoning) {
        var reasonDiv = document.createElement('div');
        reasonDiv.className = 'fp-tooltip-reasoning';
        reasonDiv.textContent = reasoning;
        tip.appendChild(reasonDiv);
      }

      var actions = document.createElement('div');
      actions.className = 'fp-tooltip-actions';

      var applyBtn = document.createElement('button');
      applyBtn.className = 'fp-tooltip-btn fp-tooltip-apply';
      applyBtn.textContent = 'Apply';
      applyBtn.onclick = function() {
        var el = document.querySelector(field.selector);
        if (el) {
          el.value = value;
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
          el.focus();
        }
        dismissTooltip();
      };

      var dismissBtn = document.createElement('button');
      dismissBtn.className = 'fp-tooltip-btn fp-tooltip-dismiss';
      dismissBtn.textContent = 'Dismiss';
      dismissBtn.onclick = function() { dismissTooltip(); };

      actions.appendChild(applyBtn);
      actions.appendChild(dismissBtn);
      tip.appendChild(actions);
    }

    document.body.appendChild(tip);
    activeTooltip = tip;

    var rect = btn.getBoundingClientRect();
    tip.style.position = 'fixed';
    tip.style.top = (rect.bottom + 6) + 'px';
    tip.style.left = Math.max(8, rect.left - 40) + 'px';

    setTimeout(function() {
      function closer(e) {
        if (!tip.contains(e.target) && e.target !== btn) {
          dismissTooltip();
          document.removeEventListener('mousedown', closer, true);
        }
      }
      document.addEventListener('mousedown', closer, true);
    }, 50);
  }

  /**
   * Request a single-field AI suggestion via the background script.
   */
  function requestFieldSuggestion(btn, field) {
    btn.classList.add('fp-loading');
    btn.textContent = '';

    var allFields = cachedFields || getFields();
    var nearbyFields = allFields
      .filter(function(f) { return f.selector !== field.selector; })
      .slice(0, 8)
      .map(function(f) {
        var el = document.querySelector(f.selector);
        return {
          label: f.label || f.placeholder || f.name || '',
          name: f.name || '',
          semanticType: f.semanticType || '',
          value: el ? (el.value || '') : (f.value || ''),
        };
      });

    var targetEl = document.querySelector(field.selector);
    var targetField = Object.assign({}, field);
    if (targetEl) targetField.value = targetEl.value || '';

    chrome.runtime.sendMessage({
      type: 'FORMPILOT_SUGGEST_FIELD',
      field: targetField,
      nearbyFields: nearbyFields,
    }, function(response) {
      btn.classList.remove('fp-loading');
      btn.textContent = '✦';
      if (response && response.ok) {
        showTooltip(btn, field, response.value, response.reasoning);
      } else {
        showTooltip(btn, field, null, 'Could not get suggestion. Check your connection.');
      }
    });
  }

  /**
   * Create a sparkle button for a field and position it.
   */
  function createSparkleForField(field) {
    if (sparkleButtons.has(field.selector)) return;

    var el = document.querySelector(field.selector);
    if (!el) return;

    var btn = document.createElement('button');
    btn.className = 'fp-sparkle-btn';
    btn.textContent = '✦';
    btn.title = 'AI suggest value for this field';
    btn.setAttribute('data-fp-sparkle', field.selector);

    btn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      requestFieldSuggestion(btn, field);
    });

    document.body.appendChild(btn);
    sparkleButtons.set(field.selector, btn);

    positionSparkle(btn, el);
  }

  /**
   * Position a sparkle button relative to its form field.
   */
  function positionSparkle(btn, el) {
    var rect = el.getBoundingClientRect();
    btn.style.position = 'fixed';
    btn.style.top = (rect.top + (rect.height / 2) - 11) + 'px';
    btn.style.left = (rect.right + 4) + 'px';

    if (rect.right + 30 > window.innerWidth) {
      btn.style.left = (rect.right - 28) + 'px';
    }
  }

  /**
   * Reposition all sparkle buttons (e.g. on scroll/resize).
   */
  function repositionSparkles() {
    sparkleButtons.forEach(function(btn, selector) {
      var el = document.querySelector(selector);
      if (el) {
        positionSparkle(btn, el);
      } else {
        btn.remove();
        sparkleButtons.delete(selector);
      }
    });
  }

  var repositionTimer = null;
  function debouncedReposition() {
    if (repositionTimer) clearTimeout(repositionTimer);
    repositionTimer = setTimeout(repositionSparkles, 100);
  }
  window.addEventListener('scroll', debouncedReposition, true);
  window.addEventListener('resize', debouncedReposition);

  /**
   * Detect form fields and place sparkle buttons. No API calls.
   */
  function observeFields() {
    var fields = getFields();
    fields.forEach(function(f) {
      createSparkleForField(f);
    });
    return fields;
  }

  /**
   * Watch for dynamically added form fields.
   */
  function initMutationObserver() {
    if (mutationObserver) return;

    var debounceTimer = null;

    mutationObserver = new MutationObserver(function(mutations) {
      var hasNewNodes = mutations.some(function(m) {
        return m.addedNodes.length > 0;
      });

      if (hasNewNodes) {
        if (debounceTimer) clearTimeout(debounceTimer);
        debounceTimer = setTimeout(function() {
          observeFields();
        }, 500);
      }
    });

    mutationObserver.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  // WebMCP message handling
  var WEBMCP_PREFIX = 'FORMPILOT_WEBMCP_';
  window.addEventListener('message', function(e) {
    if (e.source !== window) return;

    if (e.data && e.data.type === WEBMCP_PREFIX + 'RUN') {
      var requestId = e.data.requestId;
      var fields = e.data.fields || [];
      var mappings = e.data.mappings || [];
      var clearWrong = e.data.clearWrong !== false;

      try {
        var result = validateAfterFill(fields, mappings, clearWrong);
        window.postMessage({ type: WEBMCP_PREFIX + 'RESULT', requestId: requestId, result: result }, '*');
      } catch (err) {
        window.postMessage({ type: WEBMCP_PREFIX + 'RESULT', requestId: requestId, result: { ok: false, error: String(err.message) } }, '*');
      }
    }

    if (e.data && e.data.type === WEBMCP_PREFIX + 'FILL_FIELD') {
      var requestId3 = e.data.requestId;
      var selector = e.data.selector;
      var value = e.data.value;

      try {
        var el = document.querySelector(selector);
        if (!el) {
          window.postMessage({ type: WEBMCP_PREFIX + 'FILL_FIELD_RESULT', requestId: requestId3, result: { ok: false, error: 'Element not found' } }, '*');
          return;
        }

        el.value = value;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));

        window.postMessage({ type: WEBMCP_PREFIX + 'FILL_FIELD_RESULT', requestId: requestId3, result: { ok: true, filled: true } }, '*');
      } catch (err) {
        window.postMessage({ type: WEBMCP_PREFIX + 'FILL_FIELD_RESULT', requestId: requestId3, result: { ok: false, error: String(err.message) } }, '*');
      }
    }
  });

  function injectWebMCPBridge() {
    if (document.documentElement.getAttribute('data-formpilot-webmcp-injected')) return;
    document.documentElement.setAttribute('data-formpilot-webmcp-injected', 'true');
    var script = document.createElement('script');
    script.src = chrome.runtime.getURL('injected/webmcp-validate.js');
    script.onload = function() { script.remove(); };
    (document.head || document.documentElement).appendChild(script);
  }
  injectWebMCPBridge();

  // Chrome extension message handling
  chrome.runtime.onMessage.addListener(function(msg, _sender, sendResponse) {
    if (msg.type === 'FORMPILOT_GET_PAGE_FIELDS') {
      try {
        sendResponse({ ok: true, fields: getFields() });
      } catch (e) {
        sendResponse({ ok: false, error: e.message });
      }
    } else if (msg.type === 'FORMPILOT_FILL_FIELDS') {
      try {
        var filled = fillFields(msg.mappings || []);
        sendResponse({ ok: true, filled: filled });
      } catch (e) {
        sendResponse({ ok: false, error: e.message });
      }
    } else if (msg.type === 'FORMPILOT_VALIDATE_AFTER_FILL') {
      try {
        var fields = msg.fields || [];
        var mappings = msg.mappings || [];
        var clearWrong = msg.clearWrong !== false;
        var result = validateAfterFill(fields, mappings, clearWrong);
        sendResponse({ ok: true, errors: result.errors, fixedCount: result.fixedCount });
      } catch (e) {
        sendResponse({ ok: false, error: e.message });
      }
    } else if (msg.type === 'FORMPILOT_SHOW_OVERLAYS') {
      observeFields();
      sendResponse({ ok: true });
    } else {
      sendResponse({ ok: false, error: 'Unknown message type' });
    }
    return true;
  });

  // Initialize on load — detect fields, place sparkle icons. Zero API calls.
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      observeFields();
      initMutationObserver();
    });
  } else {
    observeFields();
    initMutationObserver();
  }
})();
