#!/usr/bin/env node
/**
 * blast-radius.js — 符号影响面分析（架构自检取证工具）
 *
 * 给一个符号（类名/方法名/组件名/hook 名），全仓搜出所有引用点，按角色
 * 分类（定义处 def / 调用方 call / 一般引用 ref），并提示疑似同义符号
 * （重复抽象线索）。agent 在改动/新增符号前手动跑一次，拿清单据实回答
 * 架构三问：是否分层穿越？是否已有同类抽象可复用？是否在多处糊特判？
 *
 * 用法：
 *   node blast-radius.js <symbol> [--root <path>] [--lang java|ts|py|go] [--json]
 *
 * 退出码：
 *   0 = 找到引用（有输出）
 *   2 = 0 命中——这本身是信号：仓里查不到该符号，可能在臆造，
 *       停下核实（"事实缺失即停止"）
 *
 * 触发模式：仅手动调用，不进 PostToolUse 管道（每次写代码自动全仓扫
 * 符号太吵、大仓有性能压力）。
 *
 * 依赖：仅 Node 标准库（纯进程内递归扫描，不依赖外部搜索工具）。
 */

const fs = require('fs');
const path = require('path');

// ─── 参数解析 ─────────────────────────────────────────────────────────────
const argv = process.argv.slice(2);
const positional = argv.filter(a => !a.startsWith('--'));
const symbol = positional[0];

if (!symbol || symbol.length > 200) {
  console.error('用法: node blast-radius.js <symbol> [--root <path>] [--lang java|ts|py|go] [--json]');
  console.error('示例: node blast-radius.js submitOrder --root ./src --lang ts');
  process.exit(2);
}

function getFlag(name) {
  const i = argv.indexOf('--' + name);
  if (i < 0) return null;
  const eq = argv[i].indexOf('=');
  if (eq > 0) return argv[i].slice(eq + 1);
  const next = argv[i + 1];
  return next && !next.startsWith('--') ? next : null;
}

const root = path.resolve(getFlag('root') || '.');
const lang = getFlag('lang');
const asJson = argv.includes('--json');

if (!fs.existsSync(root)) {
  console.error(`[blast-radius] 搜索根目录不存在: ${root}`);
  process.exit(2);
}

const LANG_EXT = {
  java: ['.java'],
  ts:   ['.ts', '.tsx', '.js', '.jsx'],
  py:   ['.py'],
  go:   ['.go'],
};
const exts = lang ? LANG_EXT[lang] : null;
if (lang && !exts) {
  console.error(`[blast-radius] 不支持的语言: ${lang}（可选 java|ts|py|go）`);
  process.exit(2);
}

const SKIP_DIRS = new Set([
  'node_modules', '.next', '.git', 'dist', 'build', 'target',
  'output', '.idea', '.vscode', '__pycache__',
]);

function escapeRe(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// ─── 定义 vs 调用 的正则启发式 ────────────────────────────────────────────
// 不是 AST 精确解析，是够架构三问用的启发式：
//   定义 = 符号前有声明关键字（class/function/const/def/func/public...）
//   调用 = 符号后紧跟 (
function classifyMatch(line, sym) {
  const trimmed = line.trim();
  const defRe = new RegExp(
    '\\b(class|interface|enum|struct|trait|void|int|long|boolean|String|' +
    'public|private|protected|internal|static|final|async|function|const|let|var|def|func)\\b' +
    '\\s+[\\w<>\\[\\],\\s]*' + escapeRe(sym) + '\\s*[\\(<: =]',
    'i'
  );
  const callRe = new RegExp('(\\.|\\b)' + escapeRe(sym) + '\\s*\\(');
  if (defRe.test(trimmed)) return 'def';
  if (callRe.test(trimmed)) return 'call';
  return 'ref';  // import、类型引用、注释提及
}

// ─── 疑似同义符号：常见动词前缀 × 词尾（重复抽象线索）────────────────────
function suggestSynonyms(sym) {
  const parts = sym.replace(/([a-z])([A-Z])/g, '$1 $2').split(/[\s_-]+/);
  const tail = parts[parts.length - 1];
  if (tail.length < 4) return [];
  const prefixes = ['get', 'fetch', 'load', 'query', 'create', 'build', 'make',
    'update', 'modify', 'set', 'save', 'submit', 'send', 'handle', 'process',
    'run', 'execute', 'start', 'init', 'remove', 'delete'];
  const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
  return prefixes.map(p => p + cap(tail)).filter(s => s !== sym);
}

// ─── 进程内递归扫描 ────────────────────────────────────────────────────────
function walk(dir, out) {
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch (e) {
    return;
  }
  for (const ent of entries) {
    if (SKIP_DIRS.has(ent.name) || ent.name.startsWith('.')) continue;
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) walk(p, out);
    else if (ent.isFile() && (!exts || exts.includes(path.extname(ent.name)))) out.push(p);
  }
}

const symRe = new RegExp(escapeRe(symbol));
const hits = [];
{
  const files = [];
  walk(root, files);
  for (const f of files) {
    let content;
    try {
      content = fs.readFileSync(f, 'utf-8');
    } catch (e) {
      continue;
    }
    const arr = content.split(/\r?\n/);
    for (let i = 0; i < arr.length; i++) {
      if (symRe.test(arr[i])) {
        hits.push({
          file: f.replace(/\\/g, '/'),
          line: i + 1,
          text: arr[i],
          role: classifyMatch(arr[i], symbol),
        });
      }
    }
  }
}

// ─── 汇总输出 ─────────────────────────────────────────────────────────────
if (hits.length === 0) {
  const msg = `[blast-radius] 0 命中（symbol=${symbol}, root=${root}）。仓里查不到该符号——可能在臆造，先核实再动手。`;
  console.error(msg);
  process.exit(2);
}

const byRole = { def: [], call: [], ref: [] };
for (const h of hits) byRole[h.role].push(h);
const synonyms = suggestSynonyms(symbol)
  .filter(s => hits.some(h => h.text.includes(s)))
  .slice(0, 5);

if (asJson) {
  console.log(JSON.stringify({ symbol, root, total: hits.length, byRole, synonyms }, null, 2));
} else {
  console.log(`[blast-radius] ${symbol}: ${hits.length} 处引用（def ${byRole.def.length} / call ${byRole.call.length} / ref ${byRole.ref.length}）`);
  const show = (role, label, cap) => {
    if (!byRole[role].length) return;
    console.log(`\n— ${label}（${byRole[role].length}${byRole[role].length > cap ? `，仅显示前 ${cap}` : ''}）—`);
    for (const h of byRole[role].slice(0, cap)) {
      console.log(`  ${h.file}:${h.line}  ${h.text.trim().slice(0, 100)}`);
    }
  };
  show('def', '定义处', 10);
  show('call', '调用方', 15);
  show('ref', '其他引用', 10);
  if (synonyms.length) {
    console.log(`\n— 疑似同义符号（重复抽象线索，考虑复用/合并）—`);
    console.log(`  ${synonyms.join(', ')}`);
  }
}
process.exit(0);
