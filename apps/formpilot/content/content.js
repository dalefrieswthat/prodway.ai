/**
 * FormPilot content script — WebMCP-style with inline overlays.
 * Shows Apply/Edit/Deny overlays above form fields as they scroll into view.
 * Uses IntersectionObserver for lazy suggestion loading.
 */
(function () {
  var SCRIPT_TAG = 'formpilot-content';
  var SELECTORS = 'input:not([type="hidden"]):not([type="submit"]):not([type="button"]), textarea, select';

  if (document.querySelector('[data-' + SCRIPT_TAG + ']')) return;
  document.documentElement.setAttribute('data-' + SCRIPT_TAG, 'true');

  // State
  var cachedFields = null;
  var cachedMappings = new Map(); // selector -> { value, confidence }
  var pendingFieldRequests = new Set();
  var visibilityObserver = null;
  var mutationObserver = null;
  var overlaysEnabled = true;

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

      // Validate URL fields
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
   * Calculate confidence based on semantic type match
   */
  function calculateConfidence(field, value) {
    if (!field.semanticType) return 'low';
    if (!value || value.length === 0) return 'low';

    // High confidence: exact semantic match
    var highConfidenceTypes = ['email', 'phone', 'companyName', 'website', 'linkedinUrl', 'city', 'state', 'zip', 'country'];
    if (highConfidenceTypes.indexOf(field.semanticType) !== -1) return 'high';

    // Medium confidence: contextual match
    var mediumConfidenceTypes = ['contactName', 'firstName', 'lastName', 'address', 'description', 'shortDescription'];
    if (mediumConfidenceTypes.indexOf(field.semanticType) !== -1) return 'medium';

    return 'low';
  }

  /**
   * Request suggestions for visible fields from background
   */
  function requestSuggestionsForFields(visibleFields) {
    if (!visibleFields || visibleFields.length === 0) return;

    // Filter out fields we already have suggestions for or are pending
    var fieldsToRequest = visibleFields.filter(function(f) {
      return !cachedMappings.has(f.selector) && !pendingFieldRequests.has(f.selector);
    });

    if (fieldsToRequest.length === 0) return;

    // Mark as pending
    fieldsToRequest.forEach(function(f) {
      pendingFieldRequests.add(f.selector);
    });

    // Request suggestions from background
    chrome.runtime.sendMessage({
      type: 'FORMPILOT_SUGGEST_MAPPINGS',
      fields: fieldsToRequest,
    }, function(response) {
      if (!response || !response.ok) {
        fieldsToRequest.forEach(function(f) {
          pendingFieldRequests.delete(f.selector);
        });
        return;
      }

      var mappings = response.mappings || [];

      // Process mappings and show overlays
      mappings.forEach(function(m) {
        var field = fieldsToRequest.find(function(f) { return f.index === m.index; });
        if (!field || !m.value) return;

        pendingFieldRequests.delete(field.selector);

        var confidence = calculateConfidence(field, m.value);
        cachedMappings.set(field.selector, { value: m.value, confidence: confidence });

        // Show overlay if enabled
        if (overlaysEnabled && typeof FormPilotOverlay !== 'undefined') {
          FormPilotOverlay.showOverlay(field, m.value, confidence);
        }
      });

      // Clear pending for fields without mappings
      fieldsToRequest.forEach(function(f) {
        pendingFieldRequests.delete(f.selector);
      });
    });
  }

  /**
   * Initialize IntersectionObserver for lazy loading
   */
  function initVisibilityObserver() {
    if (visibilityObserver) return;

    var debounceTimer = null;
    var pendingVisible = [];

    visibilityObserver = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting && entry.target.__formpilotField) {
          pendingVisible.push(entry.target.__formpilotField);
        }
      });

      // Debounce to batch requests
      if (debounceTimer) clearTimeout(debounceTimer);
      debounceTimer = setTimeout(function() {
        if (pendingVisible.length > 0) {
          requestSuggestionsForFields(pendingVisible.slice());
          pendingVisible = [];
        }
      }, 150);
    }, {
      threshold: 0.3,
      rootMargin: '50px'
    });
  }

  /**
   * Observe all detected form fields
   */
  function observeFields() {
    var fields = getFields();

    initVisibilityObserver();

    fields.forEach(function(f) {
      var el = document.querySelector(f.selector);
      if (el && !el.__formpilotField) {
        el.__formpilotField = f;
        visibilityObserver.observe(el);
      }
    });

    return fields;
  }

  /**
   * Watch for dynamically added form fields
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

  /**
   * Get all cached suggestions
   */
  function getCachedSuggestions() {
    var suggestions = [];
    cachedMappings.forEach(function(data, selector) {
      suggestions.push({
        selector: selector,
        value: data.value,
        confidence: data.confidence
      });
    });
    return suggestions;
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

    // Handle WebMCP tool calls
    if (e.data && e.data.type === WEBMCP_PREFIX + 'GET_SUGGESTIONS') {
      var requestId2 = e.data.requestId;
      try {
        var suggestions = getCachedSuggestions();
        window.postMessage({ type: WEBMCP_PREFIX + 'GET_SUGGESTIONS_RESULT', requestId: requestId2, result: { ok: true, suggestions: suggestions } }, '*');
      } catch (err) {
        window.postMessage({ type: WEBMCP_PREFIX + 'GET_SUGGESTIONS_RESULT', requestId: requestId2, result: { ok: false, error: String(err.message) } }, '*');
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

  // Listen for overlay events
  document.addEventListener('formpilot:field-applied', function(e) {
    var detail = e.detail;
    if (detail && detail.selector) {
      cachedMappings.set(detail.selector, { value: detail.value, confidence: 'applied' });
    }
  });

  document.addEventListener('formpilot:field-denied', function(e) {
    var detail = e.detail;
    if (detail && detail.selector) {
      cachedMappings.delete(detail.selector);
    }
  });

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
    } else if (msg.type === 'FORMPILOT_GET_SUGGESTIONS') {
      try {
        sendResponse({ ok: true, suggestions: getCachedSuggestions() });
      } catch (e) {
        sendResponse({ ok: false, error: e.message });
      }
    } else if (msg.type === 'FORMPILOT_SET_OVERLAYS_ENABLED') {
      overlaysEnabled = msg.enabled !== false;
      if (!overlaysEnabled && typeof FormPilotOverlay !== 'undefined') {
        FormPilotOverlay.hideAllOverlays();
      }
      sendResponse({ ok: true });
    } else if (msg.type === 'FORMPILOT_SHOW_OVERLAYS') {
      // Manually trigger overlay display for all visible fields
      observeFields();
      sendResponse({ ok: true });
    } else {
      sendResponse({ ok: false, error: 'Unknown message type' });
    }
    return true;
  });

  // Initialize on load
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
