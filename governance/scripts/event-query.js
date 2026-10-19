#!/usr/bin/env node
/**
 * event-query.js — 治理事件流查询工具（事后聚合，只读）
 *
 * 事件流只 append（见 event-log.js），所有计数/审计/统计都在这里做。
 *
 * CLI 用法：
 *   node event-query.js --tail [N]        查看最近 N 条（默认 20）
 *   node event-query.js --chain-verify    哈希链校验（篡改可见性）
 *   node event-query.js --verify-last     最近一次本地验证凭证（DoD 核对）
 *   node event-query.js --freq            违规签名频次 Top（重复踩坑定位）
 *
 * 模块用法（被 hooks 引用）：
 *   readEvents() / readTurnEvents(sessionId) / chainVerify()
 *
 * 依赖：仅 Node 标准库。
 */

const fs = require('fs');
const crypto = require('crypto');
const { JSONL_PATH } = require('./event-log');

/** 读取全部事件（坏行跳过并告警到 stderr，不中断）。 */
function readEvents() {
  try {
    const raw = fs.readFileSync(JSONL_PATH, 'utf-8');
    const events = [];
    for (const line of raw.split('\n')) {
      if (!line.trim()) continue;
      try {
        events.push(JSON.parse(line));
      } catch (e) {
        console.error(`[governance] 事件流存在坏行（已跳过）: ${line.slice(0, 80)}`);
      }
    }
    return events;
  } catch (e) {
    return [];
  }
}

/**
 * 读取某会话"本轮"事件：最后一条 turn-summary 之后的事件。
 * 无 turn-summary 时返回该会话全部事件。
 */
function readTurnEvents(sessionId) {
  if (!sessionId) return [];
  const events = readEvents().filter(e => e.session === sessionId);
  for (let i = events.length - 1; i >= 0; i--) {
    if (events[i].type === 'turn-summary') return events.slice(i + 1);
  }
  return events;
}

/**
 * 哈希链校验：逐行验证 prev == sha256(前一行原文)。
 * @returns {{ ok: boolean, total: number, broken: number, firstBroken: number }}
 */
function chainVerify() {
  let lines;
  try {
    lines = fs.readFileSync(JSONL_PATH, 'utf-8').split('\n').filter(l => l.trim());
  } catch (e) {
    return { ok: true, total: 0, broken: 0, firstBroken: -1 };  // 无文件 = 空链 = ok
  }
  let broken = 0;
  let firstBroken = -1;
  for (let i = 1; i < lines.length; i++) {
    let expect = '';
    try {
      expect = crypto.createHash('sha256').update(lines[i - 1], 'utf-8').digest('hex');
    } catch (e) { /* 前一行坏行按断链处理 */ }
    let actual = null;
    try {
      actual = JSON.parse(lines[i]).prev || null;
    } catch (e) { /* 坏行无 prev */ }
    // 链前时代的旧事件无 prev（null）——从首条带 prev 的事件起算
    if (actual !== null && actual !== expect) {
      broken++;
      if (firstBroken < 0) firstBroken = i + 1;  // 1-based 行号
    }
  }
  return { ok: broken === 0, total: lines.length, broken, firstBroken };
}

/** 重复违规提示：同签名历史 ≥ N 次（含本次）返回提示文案，否则空串。 */
function buildRepeatHint(failSigs, minCount) {
  const threshold = minCount || 2;
  if (!failSigs || !failSigs.length) return '';
  const allFails = readEvents().filter(e => e.type === 'gate' && e.result === 'fail');
  const hints = [];
  for (const sig of failSigs) {
    const sigFails = allFails.filter(e => e.sig === sig);
    if (sigFails.length >= threshold) {
      const last = sigFails[sigFails.length - 1];
      hints.push(`[${sig}] 历史命中 ${sigFails.length} 次——重复踩的坑。最近：${(last.detail || '（无详情）').slice(0, 80)}`);
    }
  }
  if (!hints.length) return '';
  return `[governance 自进化提示] 以下违规是重复踩的坑（详见事件流，跑 event-query.js --freq 看全貌），请针对性修正：\n${hints.join('\n')}`;
}

// ─── CLI ──────────────────────────────────────────────────────────────────
if (require.main === module) {
  const args = process.argv.slice(2);
  console.log('🛡 QGW · governance · event-query');
  const events = readEvents();

  if (args.includes('--chain-verify')) {
    const r = chainVerify();
    if (r.total === 0) {
      console.log('事件流为空（无链可验）。');
    } else if (r.ok) {
      console.log(`✅ 哈希链完整：${r.total} 条事件，0 断链。`);
    } else {
      console.log(`❌ 哈希链断裂：${r.broken} 处（首次在第 ${r.firstBroken} 行）。事件可能被改动，请人工核查。`);
      process.exitCode = 1;
    }
  } else if (args.includes('--verify-last')) {
    const vers = events.filter(e => e.type === 'verify');
    if (!vers.length) {
      console.log('（尚无验证凭证事件）');
    } else {
      const last = vers[vers.length - 1];
      console.log(`最近验证：result=${last.result} script=${last.script} ts=${last.ts}`);
      console.log(`detail: ${last.detail || '(无)'}`);
    }
  } else if (args.includes('--freq')) {
    const freq = {};
    for (const e of events) {
      if (e.type === 'gate' && e.result === 'fail' && e.sig) {
        freq[e.sig] = (freq[e.sig] || 0) + 1;
      }
    }
    const rows = Object.entries(freq).sort((a, b) => b[1] - a[1]);
    if (!rows.length) {
      console.log('（尚无失败事件）');
    } else {
      console.log('违规签名频次 Top（重复踩的坑优先治理）：');
      for (const [sig, n] of rows.slice(0, 20)) console.log(`  ${String(n).padStart(4)}  ${sig}`);
    }
  } else {
    const tailIdx = args.indexOf('--tail');
    const n = tailIdx >= 0 ? parseInt(args[tailIdx + 1], 10) || 20 : 20;
    for (const e of events.slice(-n)) {
      const head = [e.ts, e.type, e.result || e.injected || ''].filter(Boolean).join(' ');
      console.log(head + (e.sig ? ` sig=${e.sig}` : '') + (e.file ? ` file=${e.file}` : ''));
    }
    if (!events.length) console.log('（事件流为空）');
  }
}

module.exports = { readEvents, readTurnEvents, chainVerify, buildRepeatHint };
