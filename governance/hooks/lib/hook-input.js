/**
 * hook-input.js — hook stdin 信封字段归一（所有 hook 共用）
 *
 * 不同宿主/版本的 hook stdin 信封字段命名不一致（snake_case 的
 * session_id/tool_name/tool_input 与 camelCase 的 sessionId/toolName/toolInput
 * 均存在）。这里统一归一为 snake_case 口径，调用方只读 snake 字段。
 * 工具自身参数（tool_input.file_path 等）本就是 snake，不受影响。
 */

function normalizeHookInput(input) {
  if (!input || typeof input !== 'object') return input;
  if (input.session_id === undefined) input.session_id = input.sessionId || '';
  if (input.tool_name === undefined) input.tool_name = input.toolName || '';
  if (input.tool_input === undefined) input.tool_input = input.toolInput || {};
  // model：stdin 一旦带上即转 env，事件流无需改动即可全量携带
  if (input.model && !process.env.ZCODE_MODEL) process.env.ZCODE_MODEL = input.model;
  return input;
}

module.exports = { normalizeHookInput };
