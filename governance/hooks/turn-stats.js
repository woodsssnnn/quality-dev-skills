#!/usr/bin/env node
/**
 * turn-stats.js — Stop hook（governance 运行时）
 *
 * 每轮 agent 回复结束时触发，输出本轮治理干预的单行统计。
 *
 * 关键约束（死循环防范）：
 *   Stop hook 的 stdout 会被注入对话、触发 agent 继续（最多 3 次）。
 *   本 hook 只输出到 **stderr**（日志/transcript 可见，不触发 agent
 *   继续），stdout 永远为空。
 *
 * 数据源：复用事件流 jsonl（PostToolUse 已写入的 gate/summary 事件）。
 * 轮边界：上一条 turn-summary 的 ts 之后 → 本轮事件。
 *
 * 退出码：永远 exit 0（统计 hook 绝不阻断 agent）。
 */

const fs = require('fs');
const { normalizeHookInput } = require('./lib/hook-input.js');
const { readTurnEvents } = require('../scripts/event-query.js');
const evolog = require('../scripts/event-log.js');

let raw = '';
try {
  raw = fs.readFileSync(0, 'utf-8');
} catch (e) {
  process.exit(0);  // 无 stdin（非 hook 调用）→ 静默
}

let input;
try {
  input = JSON.parse(raw);
} catch (e) {
  process.exit(0);  // JSON 解析失败 → 静默
}
input = normalizeHookInput(input);

const sessionId = input.session_id || process.env.CLAUDE_SESSION_ID || '';
if (!sessionId) process.exit(0);  // 无 session 无法统计 → 静默

try {
  const events = readTurnEvents(sessionId);
  if (events.length === 0) process.exit(0);  // 本轮无事件 → 静默（不打扰）

  let gateCount = 0;        // 编辑类门禁触发次数（summary 的 pass/mixed/warn-only）
  let blockedCount = 0;     // block 拦载数（gate fail 事件）
  let hintCount = 0;        // 提示注入次数（turn-start.injected 非空 / hint 事件）
  let verifyPassCount = 0;  // 本地验证通过次数（verify 事件 result=pass）
  const fileSet = new Set();

  for (const e of events) {
    if (e.type === 'verify' && e.result === 'pass') {
      verifyPassCount++;
    } else if (e.type === 'summary') {
      if (e.track !== 'read') {
        gateCount++;
        if (e.file) fileSet.add(e.file);
      }
    } else if (e.type === 'gate' && e.result === 'fail') {
      blockedCount++;
    } else if (e.type === 'turn-start' && e.injected) {
      hintCount++;
    }
  }

  // 门禁 0 且无提示 → 本轮治理未干预，不打扰
  if (gateCount === 0 && hintCount === 0) process.exit(0);

  const parts = [];
  if (gateCount > 0) parts.push(`门禁 ${gateCount} 次`);
  if (blockedCount > 0) parts.push(`拦截 ${blockedCount}`);
  if (hintCount > 0) parts.push(`提示 ${hintCount} 次`);
  if (fileSet.size > 0) parts.push(`涉及 ${fileSet.size} 文件`);
  // DoD 提醒：有编辑门禁但本轮无通过的本地验证 → 提醒（stderr 非阻断）。
  // 方向保守：无 pass 即提醒（verify 失败/unknown 同样触发），宁多提醒不漏判。
  if (gateCount > 0 && verifyPassCount === 0) {
    parts.push('编辑未验证（完成前请跑本地验证并留下凭证）');
  }

  const line = `[governance 统计] 本轮：${parts.join(' / ')}`;
  console.error(line);  // stderr，不触发 agent 继续

  // 写 turn-summary 标记（下一轮的边界）
  evolog.logTurnSummary({
    session: sessionId,
    stats: { gateCount, blockedCount, hintCount, verifyPassCount, files: fileSet.size },
  });
} catch (e) {
  // 统计失败绝不阻断 agent，但留可观测信号
  console.error('[governance] 统计 hook 异常: ' + e.message);
}

process.exit(0);
