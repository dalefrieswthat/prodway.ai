(function () {
  if (typeof navigator === 'undefined' || !navigator.modelContext) return;
  var PREFIX = 'FORMPILOT_WEBMCP_';

  function sendAndWait(type, data, resultType) {
    var requestId = PREFIX + Math.random().toString(36).slice(2);
    return new Promise(function(resolve) {
      var handler = function(e) {
        if (!e.data || e.data.type !== resultType || e.data.requestId !== requestId) return;
        window.removeEventListener('message', handler);
        var result = e.data.result || { ok: false, error: 'No result' };
        resolve({ content: [{ type: 'text', text: JSON.stringify(result) }] });
      };
      window.addEventListener('message', handler);
      var msg = { type: type, requestId: requestId };
      Object.keys(data).forEach(function(k) { msg[k] = data[k]; });
      window.postMessage(msg, '*');
    });
  }

  navigator.modelContext.registerTool({
    name: 'formpilot_get_suggestions',
    description: 'Get AI suggestions for form fields',
    inputSchema: { type: 'object', properties: {} },
    execute: function() {
      return sendAndWait(PREFIX + 'GET_SUGGESTIONS', {}, PREFIX + 'GET_SUGGESTIONS_RESULT');
    },
  });

  navigator.modelContext.registerTool({
    name: 'formpilot_fill_field',
    description: 'Fill a form field by selector',
    inputSchema: {
      type: 'object',
      properties: {
        selector: { type: 'string' },
        value: { type: 'string' },
      },
      required: ['selector', 'value'],
    },
    execute: function(args) {
      return sendAndWait(PREFIX + 'FILL_FIELD', { selector: args.selector, value: args.value }, PREFIX + 'FILL_FIELD_RESULT');
    },
  });

  navigator.modelContext.registerTool({
    name: 'formpilot_validate_fill',
    description: 'Validate filled fields',
    inputSchema: {
      type: 'object',
      properties: {
        fields: { type: 'array' },
        mappings: { type: 'array' },
        clearWrong: { type: 'boolean', default: true },
      },
      required: ['fields', 'mappings'],
    },
    execute: function(args) {
      return sendAndWait(PREFIX + 'RUN', { fields: args.fields || [], mappings: args.mappings || [], clearWrong: args.clearWrong !== false }, PREFIX + 'RESULT');
    },
  });

  navigator.modelContext.registerTool({
    name: 'formpilot_get_fields',
    description: 'Detect all form fields on page',
    inputSchema: { type: 'object', properties: {} },
    execute: function() {
      return sendAndWait(PREFIX + 'GET_FIELDS', {}, PREFIX + 'GET_FIELDS_RESULT');
    },
  });
})();
