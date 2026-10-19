#!/usr/bin/env node
/**
 * prompt-inject.js — UserPromptSubmit hook（governance 运行时）
 *
 * 每轮用户提交 prompt 时触发。技能（skill）只能由模型自主加载、无法强制
 * 触发——本 hook 在配置命中的语境关键词出现时注入提示（additionalContext，
 * 非阻断），是"下行知识注入"的强制通道。
 *
 * 关键词与提示文案全部来自配置（promptMessages 列表，见 config.default.json
 * 与 README），内置默认为空——不配置则本 hook 立即退出、零噪音。
 *
 * 同时记录一条 turn-start 事件（Stop hook 的 turn-stats 据此划分轮次）。
 *
 * 退出码：永远 exit 0（纯引导，不阻断）。
 */

const fs = require('fs');
const { normalizeHookInput } = require('./lib/hook-input.js');
const { loadGovernanceConfig } = require('./lib/config.js');
const { shouldHint } = require('./lib/hint-state.js');
const evolog = require('../scripts/event-log.js');

let raw = '';
try {
  raw = fs.readFileSync(0, 'utf-8');
} catch (e) {
  process.exit(0);
}

let input;
try {
  input = JSON.parse(raw);
} catch (e) {
  process.exit(0);
}
input = normalizeHookInput(input);

const prompt = input.prompt || '';
const sessionId = input.session_id || process.env.CLAUDE_SESSION_ID || '';
const projectDir = process.env.ZCODE_PROJECT_DIR || process.env.CLAUDE_PROJECT_DIR || input.cwd || '';

try {
  const { config } = loadGovernanceConfig(projectDir);
  const messages = config.promptMessages || [];
  if (!messages.length) process.exit(0);

  // 逐条评估：pattern 命中 + 限频通过 → 注入
  const parts = [];
  const injectedKinds = [];
  for (const m of messages) {
    if (!m.pattern || !m.message) continue;
    let re;
    try { re = new RegExp(m.pattern, m.flags || ''); } catch (e) { continue; }
    if (!re.test(prompt)) continue;
    const kind = `prompt:${m.id || m.pattern}`;
    if (!shouldHint(sessionId, kind, '*', m.cap || 1)) continue;
    parts.push(m.message);
    injectedKinds.push(kind);
  }
  if (!parts.length) process.exit(0);

  process.stdout.write(JSON.stringify({ additionalContext: parts.join('\n') }));

  // 记录 turn-start（turn-stats 据此统计本轮提示数）
  try {
    evolog.logTurnStart({ session: sessionId, injected: injectedKinds.join('+') });
    for (const k of injectedKinds) {
      evolog.logHintEvent({ kind: k, message: '', session: sessionId });
    }
  } catch (e) {
    console.error('[governance] turn-start 记录异常: ' + e.message);
  }
} catch (e) {
  // 引导失败绝不阻断
  console.error('[governance] prompt 注入异常（已放行）: ' + e.message);
}

process.exit(0);
