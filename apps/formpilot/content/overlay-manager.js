/**
 * FormPilot Overlay Manager - Creates and manages inline suggestion overlays above form fields.
 * Uses Shadow DOM for style isolation. Handles Apply/Edit/Deny interactions.
 */
(function (global) {
  'use strict';

  var OVERLAY_HOST_ID = 'formpilot-overlay-host';
  var OVERLAY_ATTR = 'data-formpilot-overlay';

  // State management
  var state = {
    overlays: new Map(),
    suggestions: new Map(),
    host: null,
    shadowRoot: null,
    enabled: true,
  };

  /**
   * Get SVG icons
   */
  var ICONS = {
    logo: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>',
    check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>',
    edit: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>',
    x: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
  };

  /**
   * Get overlay CSS styles
   */
  function getOverlayStyles() {
    return '.fp-overlay-container{position:absolute;top:0;left:0}.fp-overlay{position:fixed;display:flex;align-items:center;gap:8px;padding:6px 10px;background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);border:1px solid rgba(255,255,255,0.1);border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,0.3),0 0 0 1px rgba(255,255,255,0.05);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;font-size:13px;color:#e0e0e0;pointer-events:auto;opacity:0;transform:translateY(-4px);transition:opacity 0.2s ease,transform 0.2s ease;max-width:400px;z-index:2147483647}.fp-overlay.fp-visible{opacity:1;transform:translateY(0)}.fp-overlay.fp-applied{background:linear-gradient(135deg,#0d4f3c 0%,#064e3b 100%);border-color:rgba(16,185,129,0.3)}.fp-overlay.fp-denied{opacity:0;pointer-events:none}.fp-overlay::after{content:"";position:absolute;bottom:-6px;left:20px;width:10px;height:10px;background:inherit;border:inherit;border-top:none;border-left:none;transform:rotate(45deg);clip-path:polygon(100% 0,100% 100%,0 100%)}.fp-overlay.fp-below::after{bottom:auto;top:-6px;transform:rotate(-135deg)}.fp-icon{width:18px;height:18px;flex-shrink:0}.fp-icon svg{width:100%;height:100%}.fp-suggestion{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#fff;font-weight:500}.fp-suggestion.fp-editable{background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);border-radius:4px;padding:2px 6px;outline:none;white-space:normal;overflow:visible}.fp-suggestion.fp-editable:focus{border-color:#6366f1;box-shadow:0 0 0 2px rgba(99,102,241,0.3)}.fp-actions{display:flex;gap:4px;flex-shrink:0}.fp-btn{width:26px;height:26px;border:none;border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.15s ease;padding:0}.fp-btn svg{width:14px;height:14px}.fp-btn-apply{background:#10b981;color:white}.fp-btn-apply:hover{background:#059669;transform:scale(1.05)}.fp-btn-edit{background:rgba(255,255,255,0.1);color:#a5b4fc}.fp-btn-edit:hover{background:rgba(255,255,255,0.2)}.fp-btn-deny{background:rgba(255,255,255,0.1);color:#f87171}.fp-btn-deny:hover{background:rgba(239,68,68,0.2)}.fp-applied-badge{display:flex;align-items:center;gap:4px;color:#10b981;font-weight:500}.fp-applied-badge svg{width:16px;height:16px}.fp-confidence{width:6px;height:6px;border-radius:50%;flex-shrink:0}.fp-confidence-high{background:#10b981}.fp-confidence-medium{background:#f59e0b}.fp-confidence-low{background:#6b7280}';
  }

  /**
   * Initialize the overlay host with Shadow DOM
   */
  function initHost() {
    if (state.host) return state.shadowRoot;

    state.host = document.createElement('div');
    state.host.id = OVERLAY_HOST_ID;
    state.host.style.cssText = 'position:absolute;top:0;left:0;z-index:2147483647;pointer-events:none;';
    document.body.appendChild(state.host);

    state.shadowRoot = state.host.attachShadow({ mode: 'open' });

    // Inject styles into shadow DOM
    var style = document.createElement('style');
    style.textContent = getOverlayStyles();
    state.shadowRoot.appendChild(style);

    // Container for all overlays
    var container = document.createElement('div');
    container.className = 'fp-overlay-container';
    state.shadowRoot.appendChild(container);

    // Reposition on scroll/resize
    var rafId = null;
    var repositionAll = function() {
      if (rafId) return;
      rafId = requestAnimationFrame(function() {
        rafId = null;
        state.overlays.forEach(function(data, selector) {
          var el = document.querySelector(selector);
          if (el && data.overlayEl) {
            positionOverlay(data.overlayEl, el);
          }
        });
      });
    };

    window.addEventListener('scroll', repositionAll, { passive: true });
    window.addEventListener('resize', repositionAll, { passive: true });

    return state.shadowRoot;
  }

  /**
   * Position an overlay above a form field
   */
  function positionOverlay(overlayEl, fieldEl) {
    var rect = fieldEl.getBoundingClientRect();
    var overlayHeight = overlayEl.offsetHeight || 40;

    overlayEl.style.left = rect.left + 'px';
    overlayEl.style.top = (rect.top - overlayHeight - 10) + 'px';

    // Ensure overlay doesn't go off-screen
    var overlayRect = overlayEl.getBoundingClientRect();
    if (overlayRect.left < 8) {
      overlayEl.style.left = '8px';
    }
    if (overlayRect.right > window.innerWidth - 8) {
      overlayEl.style.left = (window.innerWidth - overlayRect.width - 8) + 'px';
    }
    if (overlayRect.top < 8) {
      // Position below field instead
      overlayEl.style.top = (rect.bottom + 10) + 'px';
      overlayEl.classList.add('fp-below');
    } else {
      overlayEl.classList.remove('fp-below');
    }
  }

  /**
   * Escape HTML
   */
  function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  /**
   * Truncate string
   */
  function truncate(str, len) {
    if (!str || str.length <= len) return str;
    return str.slice(0, len - 1) + '\u2026';
  }

  /**
   * Apply value to form field
   */
  function applyValue(field, value) {
    var el = document.querySelector(field.selector);
    if (!el) return false;

    el.value = value;
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));

    // Update state
    var data = state.overlays.get(field.selector);
    if (data) {
      data.status = 'applied';
      data.appliedValue = value;
    }

    // Emit event for content script
    document.dispatchEvent(new CustomEvent('formpilot:field-applied', {
      detail: { selector: field.selector, value: value, field: field }
    }));

    return true;
  }

  /**
   * Show applied state on overlay
   */
  function showAppliedState(overlay) {
    overlay.classList.add('fp-applied');
    var actions = overlay.querySelector('.fp-actions');
    var suggestion = overlay.querySelector('.fp-suggestion');

    actions.innerHTML = '';
    suggestion.innerHTML = '<span class="fp-applied-badge">' + ICONS.check + ' Applied</span>';

    // Fade out after delay
    setTimeout(function() {
      overlay.classList.remove('fp-visible');
      setTimeout(function() { overlay.remove(); }, 200);
    }, 1500);
  }

  /**
   * Deny/dismiss overlay
   */
  function denyOverlay(field, overlay) {
    var data = state.overlays.get(field.selector);
    if (data) {
      data.status = 'denied';
    }

    overlay.classList.add('fp-denied');
    setTimeout(function() { overlay.remove(); }, 200);

    // Emit event
    document.dispatchEvent(new CustomEvent('formpilot:field-denied', {
      detail: { selector: field.selector, field: field }
    }));
  }

  /**
   * Enable inline editing of suggestion
   */
  function enableEditing(overlay, suggestionEl, fullValue) {
    suggestionEl.textContent = fullValue;
    suggestionEl.contentEditable = 'true';
    suggestionEl.classList.add('fp-editable');
    suggestionEl.focus();

    // Select all text
    var range = document.createRange();
    range.selectNodeContents(suggestionEl);
    var sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);

    // Handle Enter to apply
    function handler(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        suggestionEl.contentEditable = 'false';
        suggestionEl.classList.remove('fp-editable');
        suggestionEl.removeEventListener('keydown', handler);
        overlay.querySelector('[data-action="apply"]').click();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        suggestionEl.contentEditable = 'false';
        suggestionEl.classList.remove('fp-editable');
        suggestionEl.textContent = truncate(fullValue, 60);
        suggestionEl.removeEventListener('keydown', handler);
      }
    }
    suggestionEl.addEventListener('keydown', handler);

    // Handle blur
    suggestionEl.addEventListener('blur', function() {
      setTimeout(function() {
        if (suggestionEl.contentEditable === 'true') {
          suggestionEl.contentEditable = 'false';
          suggestionEl.classList.remove('fp-editable');
        }
      }, 100);
    }, { once: true });
  }

  /**
   * Create an overlay element for a field
   */
  function createOverlay(field, suggestion, confidence) {
    var overlay = document.createElement('div');
    overlay.className = 'fp-overlay';
    overlay.setAttribute(OVERLAY_ATTR, field.selector);

    var confidenceClass = confidence === 'high' ? 'fp-confidence-high' :
                          confidence === 'medium' ? 'fp-confidence-medium' : 'fp-confidence-low';

    overlay.innerHTML = '<span class="fp-confidence ' + confidenceClass + '" title="Confidence: ' + confidence + '"></span>' +
      '<span class="fp-icon" style="color: #6366f1;">' + ICONS.logo + '</span>' +
      '<span class="fp-suggestion" title="' + escapeHtml(suggestion) + '">' + escapeHtml(truncate(suggestion, 60)) + '</span>' +
      '<div class="fp-actions">' +
        '<button class="fp-btn fp-btn-apply" title="Apply (Enter)" data-action="apply">' + ICONS.check + '</button>' +
        '<button class="fp-btn fp-btn-edit" title="Edit" data-action="edit">' + ICONS.edit + '</button>' +
        '<button class="fp-btn fp-btn-deny" title="Deny (Esc)" data-action="deny">' + ICONS.x + '</button>' +
      '</div>';

    // Event handlers
    overlay.addEventListener('click', function(e) {
      var btn = e.target.closest('[data-action]');
      if (!btn) return;

      var action = btn.dataset.action;
      var suggestionEl = overlay.querySelector('.fp-suggestion');
      var currentValue = suggestionEl.textContent;

      if (action === 'apply') {
        var valueToApply = suggestionEl.textContent === truncate(suggestion, 60) ? suggestion : currentValue;
        applyValue(field, valueToApply);
        showAppliedState(overlay);
      } else if (action === 'edit') {
        enableEditing(overlay, suggestionEl, suggestion);
      } else if (action === 'deny') {
        denyOverlay(field, overlay);
      }
    });

    // Keyboard shortcuts when overlay is focused
    overlay.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && !e.target.classList.contains('fp-editable')) {
        e.preventDefault();
        overlay.querySelector('[data-action="apply"]').click();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        overlay.querySelector('[data-action="deny"]').click();
      }
    });

    return overlay;
  }

  /**
   * Show overlay for a field with suggestion
   */
  function showOverlay(field, suggestion, confidence) {
    if (!state.enabled) return;
    if (!confidence) confidence = 'medium';

    initHost();

    // Don't show if already has an overlay
    if (state.overlays.has(field.selector)) {
      var existing = state.overlays.get(field.selector);
      if (existing.status !== 'denied') return;
    }

    var el = document.querySelector(field.selector);
    if (!el) return;

    // Skip if field already has a value
    if (el.value && el.value.trim().length > 0) return;

    var container = state.shadowRoot.querySelector('.fp-overlay-container');
    var overlay = createOverlay(field, suggestion, confidence);
    container.appendChild(overlay);

    // Position and show
    positionOverlay(overlay, el);
    requestAnimationFrame(function() {
      overlay.classList.add('fp-visible');
    });

    // Store state
    state.overlays.set(field.selector, {
      field: field,
      suggestion: suggestion,
      confidence: confidence,
      status: 'pending',
      overlayEl: overlay,
    });

    state.suggestions.set(field.selector, suggestion);
  }

  /**
   * Hide overlay for a field
   */
  function hideOverlay(selector) {
    var data = state.overlays.get(selector);
    if (data && data.overlayEl) {
      data.overlayEl.classList.remove('fp-visible');
      setTimeout(function() {
        if (data.overlayEl && data.overlayEl.parentNode) {
          data.overlayEl.remove();
        }
        state.overlays.delete(selector);
      }, 200);
    }
  }

  /**
   * Hide all overlays
   */
  function hideAllOverlays() {
    state.overlays.forEach(function(data, selector) {
      hideOverlay(selector);
    });
  }

  /**
   * Get current state of all overlays
   */
  function getOverlayStates() {
    var states = [];
    state.overlays.forEach(function(data, selector) {
      states.push({
        selector: selector,
        field: data.field,
        suggestion: data.suggestion,
        status: data.status,
        appliedValue: data.appliedValue,
      });
    });
    return states;
  }

  /**
   * Enable/disable overlay system
   */
  function setEnabled(enabled) {
    state.enabled = enabled;
    if (!enabled) {
      hideAllOverlays();
    }
  }

  /**
   * Get suggestion for a field (from cache)
   */
  function getSuggestion(selector) {
    return state.suggestions.get(selector);
  }

  // Export
  global.FormPilotOverlay = {
    showOverlay: showOverlay,
    hideOverlay: hideOverlay,
    hideAllOverlays: hideAllOverlays,
    getOverlayStates: getOverlayStates,
    setEnabled: setEnabled,
    getSuggestion: getSuggestion,
    applyValue: applyValue,
  };
})(typeof window !== 'undefined' ? window : this);
