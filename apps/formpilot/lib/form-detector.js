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
    const isTextArea = el.tagName === 'TEXTAREA';
    const isTextField = el.type === 'text' || el.type === 'url' || isTextArea;

    // Contact info - high priority patterns
    if (/\bemail\b|e-?mail\b/.test(text) || el.type === 'email') return 'email';
    if (/\bphone|tel|mobile|fax\b/.test(text) || el.type === 'tel') return 'phone';

    // Video/media URLs - check before generic URL patterns
    if (/\bvideo\b|\bloom\b|\byoutube\b|\brecord.*intro|\bintroduc.*video/.test(text)) return 'videoUrl';
    if (/\bpitch\s*deck|\bdeck\b|\bslides?\b|\bpresentation\b/.test(text)) return 'pitchDeckUrl';

    // LinkedIn - specific URL type
    if (/\blinkedin\b/.test(text)) return 'linkedinUrl';

    // Twitter/X
    if (/\btwitter\b|\bx\.com\b|@\s*handle/.test(text)) return 'twitterUrl';

    // Generic website/URL - after specific URL types
    if (/\bwebsite\b|company\s*url|web\s*site\b/.test(text) && !isTextArea) return 'website';
    if (/\burl\b/.test(text) && !isTextArea && !/video|linkedin|twitter|deck/.test(text)) return 'website';

    // Company info
    if (/\bcompany\s*name\b|\borganization\s*name\b|\bbusiness\s*name\b/.test(text)) return 'companyName';
    if (/\bcompany\b|\borganization\b|\bbusiness\b|\bemployer\b/.test(text) && !isTextArea) return 'companyName';

    // Name fields
    if (/\bname\b.*\b(first|given)\b|first\s*name|given\s*name/.test(text)) return 'firstName';
    if (/\bname\b.*\b(last|family|surname)\b|last\s*name|surname/.test(text)) return 'lastName';
    if (/\bfull\s*name|your\s*name/.test(text) && !/\b(first|last)\b/.test(text)) return 'contactName';
    // Generic "name" without company context = contact name
    if (/\bname\b/.test(text) && !/company|organization|business|product/.test(text) && !isTextArea) return 'contactName';

    // Address fields
    if (/\bstreet|address\s*line|addr\b/.test(text) && !/email/.test(text)) return 'address';
    if (/\bcity|town\b/.test(text)) return 'city';
    if (/\bstate|region|province\b/.test(text)) return 'state';
    if (/\bzip|postal|postcode\b/.test(text)) return 'zip';
    if (/\bcountry\b/.test(text)) return 'country';

    // Short description / elevator pitch (typically < 500 chars)
    if (/\belevator\s*pitch\b|\bone\s*sentence\b|\bbrief(ly)?\s*describe\b|\bshort\s*description\b|\btagline\b/.test(text)) return 'shortDescription';
    if (/\bdescribe.*in\s*(one|a)\s*sentence/.test(text)) return 'shortDescription';
    if (/\bwhat\s*(do\s*you|does\s*your\s*company)\s*do\b/.test(text) && !isTextArea) return 'shortDescription';

    // Long-form descriptions (textareas asking about company)
    if (/\bdescription\b|\babout\b|\bbio\b|\boverview\b/.test(text) && isTextField) return 'description';
    if (/\bdescribe\s*(your\s*)?(company|startup|business|product)\b/.test(text) && isTextArea) return 'description';

    // Traction / metrics
    if (/\btraction\b|\bmetrics\b|\brevenue\b|\busers\b|\bgrowth\b|\bkpi\b|\barr\b|\bmrr\b/.test(text)) return 'traction';

    // Problem/solution
    if (/\bproblem\b|\bpain\s*point\b/.test(text)) return 'problemStatement';
    if (/\bsolution\b|\bhow\s*(do\s*you|does\s*it)\s*solve\b/.test(text)) return 'solutionStatement';
    if (/\bwhy\s*(now|this|build)\b|\bwhy\s*are\s*you\b/.test(text)) return 'whyNow';

    // Team / founders
    if (/\bteam\b|\bfounders?\b|\bco-?founders?\b|\bbackground\b/.test(text) && isTextArea) return 'teamDescription';

    // Funding / investment
    if (/\bfunding\b|\braise\b|\binvestment\b|\bvaluation\b/.test(text)) return 'fundingInfo';
    if (/\bhow\s*much.*rais(e|ing)\b|\bamount\s*seeking\b/.test(text)) return 'fundingAmount';

    // Market / competition
    if (/\bmarket\s*size\b|\btam\b|\bsam\b|\bsom\b/.test(text)) return 'marketSize';
    if (/\bcompetitor|\bcompetition\b|\balternative\b/.test(text)) return 'competitors';

    // YC-specific fields
    if (/\bwhat.*unique\b|\bunfair\s*advantage\b|\bmoat\b/.test(text)) return 'uniqueAdvantage';
    if (/\bhow.*hear\s*(about|of)\b|\breferr(al|ed)\b/.test(text)) return 'referralSource';

    // Investor context (for investors/YC)
    if (/\binvestor.*context\b|\bfor\s*investors\b/.test(text)) return 'investorContext';

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
