#!/usr/bin/env node
/**
 * event-log.js — 治理事件流 append 模块（被各 hook 调用）
 *
 * 职责：把门禁事件（通过/失败/验证/完整性/轮次）append 到
 * ~/.zcode/governance-data/governance-events.jsonl，一行一条 JSON。
 *
 * 设计原则（traces-as-ground-truth）：
 *   - 零读、零变异、零正则——只 append，永不修改已有行
 *   - append-only 天然契合 hook 的无状态进程模型
 *   - 计数/阈值/审计全部是对数据流的事后查询（见 event-query.js）
 *
 * 哈希链（tamper-evidence）：每条事件带 prev = 前一条原始行的 SHA-256。
 * 事件流文件处于项目 agent 的 Bash 可写范围内，append-only 是自觉不是
 * 保障；链把"悄悄改/删一行"的成本提高到"重算整条后续链"。
 * 这是篡改可见性（tamper-evidence）而非篡改防护（tamper-proofing）——
 * 无 out-of-band 锚，能改文件者理论上可重算全链。并发 append 竞态
 * 最坏产生个别断链，--chain-verify 如实报告，不禁用功能。
 *
 * 依赖：仅 Node 标准库，Node >= 12。
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const { getDataHome } = require('../hooks/lib/data-home');
const DATA_DIR = getDataHome();
const JSONL_PATH = path.join(DATA_DIR, 'governance-events.jsonl');

/** 确保数据目录存在。目录创建失败时抛错，调用方 catch 后静默跳过——
 *  事件记录失败绝不阻断 agent 主流程。 */
function ensureDataFile() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
}

/**
 * 判断事件是否来自测试夹具（__test__ 路径）。夹具里的违规是故意的
 * 反面教材，不应污染生产事件流——否则"重复违规"计数被测试虚高，
 * 真实代码命中同规则时收到误导提示。
 */
function isTestArtifact(obj) {
  const file = obj && obj.file;
  if (!file) return false;
  return /__test__[\\/]|(test|spec)[\\/]fixtures[\\/]/i.test(file);
}

/**
 * 追加一行 JSON 事件（内部）。所有公开函数最终都走这里——
 * 保证"一次调用 = 一行 JSON"。测试夹具事件不写入生产 jsonl。
 * model 惰性求值：归一化可能在本模块被 require 之后才点亮 env，
 * 顶层 const 会锁死空值；任一来源被点亮即全事件自动携带。
 */
function appendLine(obj) {
  if (isTestArtifact(obj)) return;  // 测试夹具不进生产数据
  const model = process.env.ZCODE_MODEL || process.env.CLAUDE_MODEL || process.env.ANTHROPIC_MODEL;
  if (model) obj.model = model;
  const prevLine = lastRawLine();
  if (prevLine !== null) obj.prev = crypto.createHash('sha256').update(prevLine, 'utf-8').digest('hex');
  ensureDataFile();
  fs.appendFileSync(JSONL_PATH, JSON.stringify(obj) + '\n', 'utf-8');
}

// 取文件最后一条非空原始行（链的前驱）。文件不存在/为空返回 null
//（首条为链锚，不带 prev）。
function lastRawLine() {
  try {
    if (!fs.existsSync(JSONL_PATH)) return null;
    const lines = fs.readFileSync(JSONL_PATH, 'utf-8').split('\n');
    for (let i = lines.length - 1; i >= 0; i--) {
      if (lines[i].trim()) return lines[i];
    }
    return null;
  } catch (e) {
    return null;
  }
}

/** 记录一条门禁事件。result: 'pass' | 'fail'；sig: '规则集/规则ID'。 */
function logGateEvent(e) {
  appendLine({
    ts: new Date().toISOString(),
    type: 'gate',
    result: e.result,
    ruleSet: e.ruleSet || '',
    rule: e.rule || '',
    sig: e.sig || '',
    file: e.file || '',
    session: e.session || '',
    detail: (e.detail || '').slice(0, 200),
  });
}

/** 记录一条汇总事件。result: 'pass'（全过）| 'mixed'（部分过部分败）| 'warn-only'。 */
function logSummary(e) {
  appendLine({
    ts: new Date().toISOString(),
    type: 'summary',
    result: e.result,
    passed: e.passed || [],
    failed: e.failed || 0,
    warned: e.warned || 0,
    file: e.file || '',
    track: e.track || 'edit',
    session: e.session || '',
  });
}

/**
 * 记录一次本地验证运行（DoD 审计链）。
 * 由 run-checks 的 Bash 分支在检测到验证命令调用时补记——验证脚本
 * 经 Bash 工具运行、拿不到 session（非 hook 进程），hook 侧补记是唯一
 * 带 session 的机器凭证，reviewer 据此核对"验证真的跑过且通过"。
 */
function logVerifyEvent(e) {
  appendLine({
    ts: new Date().toISOString(),
    type: 'verify',
    result: e.result || 'unknown',   // 'pass' | 'fail' | 'unknown'
    script: e.script || '',
    detail: (e.detail || '').slice(0, 400),
    session: e.session || '',
    project: e.project || '',
  });
}

/** 记录一次提示注入事件（哪条提示被下发，曝光量事后可查）。 */
function logHintEvent(e) {
  appendLine({
    ts: new Date().toISOString(),
    type: 'hint',
    kind: e.kind || '',
    message: (e.message || '').slice(0, 200),
    file: e.file || '',
    session: e.session || '',
  });
}

/** 记录一次完整性检测。result: 'ok' | 'drift' | 'skip-no-anchor' | 'error'。
 *  ok/skip 也记——审计时间线上"检测跑过且结论 X"必须可追溯。 */
function logIntegrityEvent(e) {
  appendLine({
    ts: new Date().toISOString(),
    type: 'integrity',
    result: e.result || '',
    detail: (e.detail || '').slice(0, 400),
    session: e.session || '',
  });
}

/** 记录一轮的开始（UserPromptSubmit 注入提示时）。Stop hook 据此划分轮次。 */
function logTurnStart(e) {
  appendLine({
    ts: new Date().toISOString(),
    type: 'turn-start',
    session: e.session || '',
    injected: e.injected || '',
  });
}

/** 记录一轮的结束统计快照（作为下一轮的边界标记）。 */
function logTurnSummary(e) {
  appendLine({
    ts: new Date().toISOString(),
    type: 'turn-summary',
    session: e.session || '',
    stats: e.stats || {},
  });
}

/** 记录一条洞见（从数据聚合出结论、提炼入知识库时标记）。 */
function logInsight(e) {
  appendLine({
    ts: new Date().toISOString(),
    type: 'insight',
    sig: e.sig || '',
    ref: e.ref || '',
    lesson: (e.lesson || '').slice(0, 300),
  });
}

module.exports = {
  logGateEvent, logSummary, logVerifyEvent, logHintEvent,
  logIntegrityEvent, logTurnStart, logTurnSummary, logInsight,
  isTestArtifact, JSONL_PATH,
};
