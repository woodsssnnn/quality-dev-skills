#!/usr/bin/env node
/**
 * distill-scope.js — 知识蒸馏范围计算（增量水位 + 候选教训清单）
 *
 * 治理事件流积累了原始事实；把"重复违规/高频提示"蒸馏成规则/文档需要
 * 人工审核（人审闸：工具只出候选清单，不自动改规则库）。本工具计算自
 * 上次水位以来的增量，输出候选教训清单：
 *   - 失败签名频次 Top（重复踩的坑 → 最优先蒸馏）
 *   - 提示曝光统计（哪些知识在起作用 / 从未触发）
 *   - 验证通过率（DoD 执行情况）
 *
 * 用法：
 *   node distill-scope.js            # 输出候选清单（dry-run，不动水位）
 *   node distill-scope.js --commit   # 人审通过后推进水位（只前移不回退）
 *
 * 依赖：仅 Node 标准库。
 */

const fs = require('fs');
const path = require('path');
const { readEvents } = require('./event-query.js');
const { getDataHome } = require('../hooks/lib/data-home.js');

const WATERMARK_PATH = path.join(getDataHome(), 'distill-watermark.json');
const commit = process.argv.includes('--commit');
// 只读事件流 + 写自身数据目录水位文件；不触碰任何项目源码（人审闸原则）

function readWatermark() {
  try {
    return JSON.parse(fs.readFileSync(WATERMARK_PATH, 'utf-8')).lastTs || '';
  } catch (e) {
    return '';
  }
}

// ─── 增量计算 ─────────────────────────────────────────────────────────────
const lastTs = readWatermark();
const all = readEvents();
// 增量区间：ts > 水位；测试会话（e2e- 前缀）不参与蒸馏
const events = all.filter(e =>
  (!lastTs || e.ts > lastTs) && !(e.session && /^e2e-/.test(e.session)));

let maxTs = lastTs;
const failFreq = {};      // sig -> n（重复踩的坑）
const hintKinds = {};     // kind -> n（知识下行曝光）
let verifyTotal = 0, verifyPass = 0;
const sessionSet = new Set();

for (const e of events) {
  if (e.ts > maxTs) maxTs = e.ts;
  if (e.session) sessionSet.add(e.session);

  if (e.type === 'gate' && e.result === 'fail' && e.sig) {
    failFreq[e.sig] = (failFreq[e.sig] || 0) + 1;
  } else if (e.type === 'hint' && e.kind) {
    hintKinds[e.kind] = (hintKinds[e.kind] || 0) + 1;
  } else if (e.type === 'verify') {
    verifyTotal++;
    if (e.result === 'pass') verifyPass++;
  }
}

// ─── 输出候选清单（markdown，供人审）──────────────────────────────────────
const lines = [];
lines.push(`# 蒸馏候选清单（增量自 ${lastTs || '（首次，全量）'}）`);
lines.push('');
lines.push(`- 事件范围：${events.length} 条 / ${sessionSet.size} 个会话`);
if (verifyTotal > 0) {
  lines.push(`- 验证执行：${verifyTotal} 次，通过率 ${(100 * verifyPass / verifyTotal).toFixed(0)}%`);
}
lines.push('');

const top = (obj, n) => Object.entries(obj).sort((a, b) => b[1] - a[1]).slice(0, n);
const failTop = top(failFreq, 15);
if (failTop.length) {
  lines.push('## 失败签名频次 Top（重复踩的坑，最优先蒸馏）');
  lines.push('');
  lines.push('| 签名 | 次数 | 蒸馏建议 |');
  lines.push('|------|------|----------|');
  for (const [sig, n] of failTop) {
    const advice = n >= 5 ? '→ 升级为 block 规则 + 写入错题本' : n >= 3 ? '→ 写入项目规则/文档' : '→ 观察';
    lines.push(`| ${sig} | ${n} | ${advice} |`);
  }
  lines.push('');
}

const hintTop = top(hintKinds, 10);
if (hintTop.length) {
  lines.push('## 提示曝光统计（知识下行通道是否在工作）');
  lines.push('');
  lines.push('| 提示 | 曝光次数 |');
  lines.push('|------|----------|');
  for (const [kind, n] of hintTop) lines.push(`| ${kind} | ${n} |`);
  lines.push('');
}

if (!failTop.length && !hintTop.length && verifyTotal === 0) {
  lines.push('（本增量区间无值得蒸馏的事件）');
}

console.log(lines.join('\n'));

// ─── 水位推进（--commit，人审通过后执行）─────────────────────────────────
if (commit) {
  if (maxTs && maxTs > (lastTs || '')) {
    fs.mkdirSync(path.dirname(WATERMARK_PATH), { recursive: true });
    fs.writeFileSync(WATERMARK_PATH, JSON.stringify({ lastTs: maxTs }, null, 2) + '\n');
    console.log(`\n✅ 水位已推进至 ${maxTs}（${WATERMARK_PATH}）`);
  } else {
    console.log('\n（无新事件，水位不变）');
  }
}
