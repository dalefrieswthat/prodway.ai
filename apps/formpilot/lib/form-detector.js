/**
 * Form field detection — WebMCP-style snapshot with stable selectors.
 * Single responsibility: detect fields, assign a stable selector per field for reliable placement.
 * No side effects other than optional data-formpilot-id injection for stability.
 */
(function (global) {
  'use strict';
  const SELECTORS = [
    'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="image"])',
    'textarea',
    'select',
  ].join(', ');
  const DATA_ID_ATTR = 'data-formpilot-id';

  function getLabelForInput(el) {
    var root = el.getRootNode ? el.getRootNode() : document;
    var id = el.id;
    if (id) {
      try {
        var label = root.querySelector('label[for="' + id.replace(/"/g, '\\"') + '"]');
        if (label) return label.textContent.replace(/\s+/g, ' ').trim();
      } catch (_) {}
    }
    var parent = el.closest ? el.closest('label') : null;
    if (parent) return parent.textContent.replace(/\s+/g, ' ').trim();
    parent = el.closest ? el.closest('div[role="group"], fieldset') : null;
    if (parent) {
      const legend = parent.querySelector('legend, [class*="label"], [class*="Label"]');
      if (legend) return legend.textContent.replace(/\s+/g, ' ').trim();
    }
    return '';
  }

  function getPlaceholder(el) {
    return (el.getAttribute('placeholder') || '').trim();
  }

  function getFieldName(el) {
    const name = el.name || el.getAttribute('aria-label') || '';
    return name.trim();
  }

  function inferSemanticType(el, label, placeholder, name) {
    const text = `${(label || '').toLowerCase()} ${(placeholder || '').toLowerCase()} ${(name || '').toLowerCase()}`;
    if (/\bemail\b|e-?mail\b/.test(text) || el.type === 'email') return 'email';
    if (/\bphone|tel|mobile|fax\b/.test(text) || el.type === 'tel') return 'phone';
    if (/\bcompany|organization|business|employer\b/.test(text)) return 'companyName';
    if (/\bname\b.*\b(first|given)\b|first\s*name|given\s*name/.test(text)) return 'contactName';
    if (/\bname\b.*\b(last|family|surname)\b|last\s*name|surname/.test(text)) return 'lastName';
    if (/\bfull\s*name|your\s*name|name\b(?!\s*of)/.test(text) && !/\b(first|last)\b/.test(text)) return 'contactName';
    if (/\bwebsite|url|web\s*site\b/.test(text)) return 'website';
    if (/\baddress|street|addr\b/.test(text)) return 'address';
    if (/\bcity|town\b/.test(text)) return 'city';
    if (/\bstate|region|province\b/.test(text)) return 'state';
    if (/\bzip|postal|postcode\b/.test(text)) return 'zip';
    if (/\bcountry\b/.test(text)) return 'country';
    if (/\blinkedin\b/.test(text)) return 'linkedinUrl';
    if (/\bdescription|about|bio\b/.test(text) && (el.tagName === 'TEXTAREA' || el.type === 'text')) return 'description';
    if (/\btraction|metrics|revenue|users\b/.test(text)) return 'traction';
    if (/\bproblem|solution|why\b/.test(text)) return 'problemSolution';
    return null;
  }

  /** Build a stable CSS selector for this element so we can fill by selector (WebMCP-style). */
  function buildStableSelector(el, index) {
    var root = el.getRootNode ? el.getRootNode() : document;
    var tag = el.tagName ? el.tagName.toLowerCase() : 'input';
    var id = el.id && el.id.trim();
    if (id && /^[a-zA-Z][\w-]*$/.test(id)) {
      try {
        if (root.querySelectorAll && root.querySelectorAll('#' + CSS.escape(id)).length === 1)
          return '#' + CSS.escape(id);
      } catch (_) {}
    }
    var name = el.getAttribute('name');
    if (name && /^[a-zA-Z][\w.-]*$/.test(name)) {
      try {
        var escaped = CSS.escape(name);
        var sel = tag + '[name="' + escaped + '"]';
        if (root.querySelectorAll && root.querySelectorAll(sel).length === 1) return sel;
      } catch (_) {}
    }
    var fpId = 'fp_' + index;
    el.setAttribute(DATA_ID_ATTR, fpId);
    return '[' + DATA_ID_ATTR + '="' + fpId + '"]';
  }

  function detectFields() {
    var elements = Array.prototype.slice.call(document.querySelectorAll(SELECTORS));
    var seen = new Set();
    var fields = [];

    elements.forEach(function (el, index) {
      if (el.type === 'hidden') return;
      const label = getLabelForInput(el);
      const placeholder = getPlaceholder(el);
      const name = getFieldName(el);
      const semanticType = inferSemanticType(el, label, placeholder, name);
      const key = `${el.tagName}-${el.name || ''}-${el.type}-${index}`;
      if (seen.has(key)) return;
      seen.add(key);

      const selector = buildStableSelector(el, index);

      fields.push({
        id: `fp_${index}_${Date.now()}`,
        index,
        selector,
        tagName: el.tagName.toLowerCase(),
        type: (el.type || 'text').toLowerCase(),
        name,
        label: label || null,
        placeholder: placeholder || null,
        semanticType,
        value: el.value || '',
      });
    });

    return fields;
  }

  global.FormPilotDetector = { detectFields };
})(typeof window !== 'undefined' ? window : this);
