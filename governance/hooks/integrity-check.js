#!/usr/bin/env node
/**
 * integrity-check.js — SessionStart hook（判题机自保护）
 *
 * 每会话启动时比对运行时目录与安装快照（锚清单），发现门禁脚本被
 * 篡改/损坏即告警。核心逻辑在 lib/integrity.js（可注入路径，供
 * --self-test 构造假目录验证检测器本身——judging the judge）。
 *
 * 纪律（与其余 hook 一致）：
 *   - 任何异常全吞 + exit 0——绝不阻断会话启动
 *   - ok/skip 静默，只有 drift 告警（stderr + additionalContext）
 *   - 全部结果落 type:'integrity' 事件（审计时间线：检测跑过没有、结论是什么）
 *
 * 用法：hook 自动调用；`node integrity-check.js --self-test` 自检（退出码 0/1）；
 *       `node integrity-check.js --write-anchor` 写安装快照（安装流程用）。
 */

const fs = require('fs');
const path = require('path');
const { snapshotTree, checkIntegrity } = require('./lib/integrity.js');
const evolog = require('../scripts/event-log.js');

const RUNTIME_ROOT = path.resolve(__dirname, '..');
const { getDataHome } = require('./lib/data-home');
const ANCHOR_PATH = path.join(getDataHome(), 'integrity-anchor.json');

// ─── self-test：五场景构造 tmp 目录验证检测器本身 ────────────────────────
function selfTest() {
  const os = require('os');
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'integrity-selftest-'));

  const mkTree = (dir, { extra = '', crlf = false } = {}) => {
    fs.mkdirSync(path.join(dir, 'hooks'), { recursive: true });
    const nl = crlf ? '\r\n' : '\n';
    fs.writeFileSync(path.join(dir, 'hooks', 'judge.js'), `const v = 1;${nl}module.exports = v;${nl}`);
    if (extra) fs.writeFileSync(path.join(dir, 'extra.txt'), extra);
  };

  const scenarios = [];
  const t = (name, dir, anchorObj, expected) => {
    const anchorPath = path.join(tmp, `anchor-${scenarios.length}.json`);
    if (anchorObj !== null) fs.writeFileSync(anchorPath, JSON.stringify(anchorObj));
    const r = checkIntegrity({ runtimeDir: dir, anchorPath });
    scenarios.push({ name, expected, actual: r.result, ok: r.result === expected, detail: r.detail });
  };

  // 1 完全一致 → ok
  let dir = path.join(tmp, 'c1');
  mkTree(dir);
  t('一致树 → ok', dir, snapshotTree(dir), 'ok');

  // 2 改一字节 → drift
  dir = path.join(tmp, 'c2');
  mkTree(dir);
  const snap2 = snapshotTree(dir);
  fs.writeFileSync(path.join(dir, 'hooks', 'judge.js'), 'const v = 2;\nmodule.exports = v;\n');
  t('改一字节 → drift', dir, snap2, 'drift');

  // 3 仅 CRLF 差异 → ok（归一生效，防假阳性）
  const dirLf = path.join(tmp, 'c3lf');
  const dirCrlf = path.join(tmp, 'c3crlf');
  mkTree(dirLf, { crlf: false });
  mkTree(dirCrlf, { crlf: true });
  t('仅 CRLF 差异 → ok（归一防假阳性）', dirCrlf, snapshotTree(dirLf), 'ok');

  // 4 锚缺失 → skip-no-anchor
  dir = path.join(tmp, 'c4');
  mkTree(dir);
  t('锚清单缺失 → skip-no-anchor', dir, null, 'skip-no-anchor');

  // 5 多出文件 → drift
  dir = path.join(tmp, 'c5');
  mkTree(dir, { extra: 'sneaky' });
  mkTree(path.join(tmp, 'c5base'));
  t('多出文件 → drift', dir, snapshotTree(path.join(tmp, 'c5base')), 'drift');

  let fail = 0;
  for (const s of scenarios) {
    console.log(`${s.ok ? '[PASS]' : '[FAIL]'} ${s.name}（${s.actual}${s.ok ? '' : ' 期望 ' + s.expected + '；' + s.detail}）`);
    if (!s.ok) fail++;
  }
  console.log(fail === 0 ? 'ALL PASS' : `SOME FAIL (${fail})`);
  return fail === 0 ? 0 : 1;
}

if (process.argv.includes('--self-test')) process.exit(selfTest());

// 写安装快照（安装/更新流程调用；hook 模式不写——检测者不能自定锚）
if (process.argv.includes('--write-anchor')) {
  const snap = snapshotTree(RUNTIME_ROOT);
  fs.writeFileSync(ANCHOR_PATH, JSON.stringify(snap, null, 2));
  console.log(`✅ 已写入安装快照（${Object.keys(snap.files).length} 文件）: ${ANCHOR_PATH}`);
  process.exit(0);
}

// hook 模式兜底：未捕获异常也绝不阻断会话启动（SessionStart 非零退出是
// 最坏故障，exit-0 契约不可破）
process.on('uncaughtException', () => process.exit(0));

// ─── hook 主体：stdin → 检测 → 落事件 → drift 告警 ───────────────────────
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
  process.exit(0);
}
const { normalizeHookInput } = require('./lib/hook-input.js');
input = normalizeHookInput(input);
const sessionId = input.session_id || process.env.CLAUDE_SESSION_ID || '';

try {
  const r = checkIntegrity({ runtimeDir: RUNTIME_ROOT, anchorPath: ANCHOR_PATH });
  evolog.logIntegrityEvent({ result: r.result, detail: r.detail, session: sessionId });

  if (r.result === 'drift') {
    const msg = `[governance integrity] 运行时文件与安装快照不一致（${r.detail}）。两种可能：文件被篡改/损坏，或运行时有未重新快照的更新。请人工核对后重新执行 integrity-check.js --write-anchor。`;
    console.error(msg);
    process.stdout.write(JSON.stringify({ additionalContext: msg }));
  }
} catch (e) {
  // 检测自身异常也要留痕（审计时间线上 error 可见），但绝不阻断
  try {
    evolog.logIntegrityEvent({ result: 'error', detail: String(e.message).slice(0, 300), session: sessionId });
  } catch (e2) { /* 事件流也坏时只能静默 */ }
}

process.exit(0);
