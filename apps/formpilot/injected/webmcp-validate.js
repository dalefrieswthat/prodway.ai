/**
 * FormPilot WebMCP bridge — runs in page context.
 * Registers a WebMCP tool so in-browser agents (or DevTools MCP) can call
 * form-fill validation. Execution is delegated to the content script via postMessage.
 */
(function () {
  if (typeof navigator === 'undefined' || !navigator.modelContext) return;
  const PREFIX = 'FORMPILOT_WEBMCP_';
  navigator.modelContext.registerTool({
    name: 'formpilot_validate_fill',
    description: 'Validate that form fields were filled correctly (DOM snapshot). Call after FormPilot fill. Clears wrong values e.g. non-URL in LinkedIn field. Returns ok, errors, fixedCount.',
    inputSchema: {
      type: 'object',
      properties: {
        fields: { type: 'array', description: 'Form field descriptors (index, selector, label, semanticType)' },
        mappings: { type: 'array', description: 'Applied mappings (index, value)' },
        clearWrong: { type: 'boolean', description: 'Clear fields with wrong value or type', default: true },
      },
      required: ['fields', 'mappings'],
    },
    async execute(args) {
      const requestId = PREFIX + Math.random().toString(36).slice(2);
      const { fields = [], mappings = [], clearWrong = true } = args;
      return new Promise((resolve) => {
        const handler = (e) => {
          if (e.data?.type !== PREFIX + 'RESULT' || e.data.requestId !== requestId) return;
          window.removeEventListener('message', handler);
          const result = e.data.result || { ok: false, error: 'No result' };
          resolve({ content: [{ type: 'text', text: JSON.stringify(result) }] });
        };
        window.addEventListener('message', handler);
        window.postMessage({
          type: PREFIX + 'RUN',
          requestId,
          fields,
          mappings,
          clearWrong,
        }, '*');
      });
    },
  });
})();
