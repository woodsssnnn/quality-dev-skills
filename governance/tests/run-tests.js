#!/usr/bin/env node
/**
 * run-tests.js — governance 运行时自测（仅 Node 标准库）
 *
 * 用法：node governance/tests/run-tests.js
 * 退出码：0 = 全部通过；1 = 有失败
 *
 * 环境隔离：GOVERNANCE_DATA_HOME / GOVERNANCE_HINT_STATE_FILE 在加载任何
 * 模块之前指向临时目录，事件流与限频状态不污染生产数据；子进程测试继承
 * 同样的环境变量。
 *
 * 夹具说明：密钥类夹具字符串用片段拼接构造（PW 常量），避免测试源码自身
 * 命中密钥检测规则。
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const assert = require('assert');
const { spawnSync } = require('child_process');

const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'governance-tests-'));
process.env.GOVERNANCE_DATA_HOME = path.join(TMP, 'data');
process.env.GOVERNANCE_HINT_STATE_FILE = path.join(TMP, 'data', 'hint-state.json');

// 密钥字段名片段：拼出完整字面量供夹具使用，测试源码不出现连续敏感模式
const PW = ['pass', 'word'].join('');

const RUNTIME_ROOT = path.resolve(__dirname, '..');
const results = [];

function test(name, fn) {
  try {
    fn();
    results.push({ name, ok: true });
    console.log(`[PASS] ${name}`);
  } catch (e) {
    results.push({ name, ok: false, err: e.message });
    console.log(`[FAIL] ${name}\n       ${e.message}`);
  }
}

// ─── 1. hook-input：stdin 信封双格式归一 ──────────────────────────────────
test('hook-input: camelCase 信封归一为 snake_case', () => {
  const { normalizeHookInput } = require('../hooks/lib/hook-input.js');
  const out = normalizeHookInput({ sessionId: 's1', toolName: 'Edit', toolInput: { file_path: '/a/b.js' } });
  assert.strictEqual(out.session_id, 's1');
  assert.strictEqual(out.tool_name, 'Edit');
  assert.deepStrictEqual(out.tool_input, { file_path: '/a/b.js' });
});

test('hook-input: snake_case 信封原样保留', () => {
  const { normalizeHookInput } = require('../hooks/lib/hook-input.js');
  const out = normalizeHookInput({ session_id: 's2', tool_name: 'Write', tool_input: {} });
  assert.strictEqual(out.session_id, 's2');
  assert.strictEqual(out.tool_name, 'Write');
});

// ─── 2. 规则引擎：内置规则加载与匹配 ──────────────────────────────────────
test('rules: 加载全部内置规则集', () => {
  const { loadRuleSets } = require('../hooks/lib/rules.js');
  const sets = loadRuleSets(null, []);
  const ids = sets.map(s => s.id);
  assert.ok(ids.includes('secret-leaks'), '应含 secret-leaks');
  assert.ok(ids.includes('debug-residue'), '应含 debug-residue');
});

test('rules: 密钥泄漏 block 命中', () => {
  const { loadRuleSets, matchContent } = require('../hooks/lib/rules.js');
  const sets = loadRuleSets(null, []);
  const file = path.join(TMP, 'app.js');
  const vs = matchContent(sets, file, `const cfg = { ${PW}: "super-secret-123" };\n`);
  const sec = vs.find(v => v.rule === 'SEC-001');
  assert.ok(sec, 'SEC-001 应命中');
  assert.strictEqual(sec.severity, 'block');
  assert.strictEqual(sec.sig, 'secret-leaks/SEC-001');
  assert.strictEqual(sec.line, 1);
});

test('rules: 私钥 PEM 命中 SEC-002', () => {
  const { loadRuleSets, matchContent } = require('../hooks/lib/rules.js');
  const sets = loadRuleSets(null, []);
  const vs = matchContent(sets, path.join(TMP, 'server.pem'),
    '-----BEGIN RSA PRIVATE KEY-----\nMIIB\n-----END RSA PRIVATE KEY-----\n');
  assert.ok(vs.find(v => v.rule === 'SEC-002'), 'SEC-002 应命中');
});

test('rules: 干净内容零命中', () => {
  const { loadRuleSets, matchContent } = require('../hooks/lib/rules.js');
  const sets = loadRuleSets(null, []);
  const vs = matchContent(sets, path.join(TMP, 'ok.js'), 'const x = 1;\nconsole.info("done");\n');
  assert.strictEqual(vs.length, 0);
});

test('rules: 扩展名过滤（.md 不跑 debug-residue）', () => {
  const { loadRuleSets, matchContent } = require('../hooks/lib/rules.js');
  const sets = loadRuleSets(null, []);
  const vs = matchContent(sets, path.join(TMP, 'notes.md'), 'console.log("x");\n');
  assert.ok(!vs.find(v => v.ruleSet === 'debug-residue'), 'md 不适用 debug-residue');
});

test('rules: 同 id 规则集后加载覆盖先加载', () => {
  const { loadRuleSets, matchContent } = require('../hooks/lib/rules.js');
  // 项目规则集覆盖内置同 id（secret-leaks 只留一条 warn 规则）
  const projDir = path.join(TMP, 'proj-override');
  fs.mkdirSync(path.join(projDir, '.qgw', 'rules'), { recursive: true });
  fs.writeFileSync(path.join(projDir, '.qgw', 'rules', 'secret-leaks.json'), JSON.stringify({
    id: 'secret-leaks', version: '1.0.0',
    appliesTo: { extensions: ['.js'] },
    rules: [{ id: 'SEC-999', severity: 'warn', pattern: 'NEVER_MATCHES_XYZ', message: 'x' }],
  }));
  const sets = loadRuleSets(projDir, []);
  const secSets = sets.filter(s => s.id === 'secret-leaks');
  assert.strictEqual(secSets.length, 1, '同 id 只留一个');
  assert.strictEqual(secSets[0].rules.length, 1);
  assert.strictEqual(secSets[0].rules[0].id, 'SEC-999');
  const vs = matchContent(sets, path.join(projDir, 'a.js'), `${PW} = "leak-me-12345";\n`);
  assert.strictEqual(vs.length, 0, '被覆盖后内置 SEC-001 不再生效');
});

// ─── 3. 配置：三层合并与领域包解析 ────────────────────────────────────────
test('config: 空项目回落到内置默认', () => {
  const { loadGovernanceConfig } = require('../hooks/lib/config.js');
  const { config, packDirs } = loadGovernanceConfig(null);
  assert.deepStrictEqual(config.packs, []);
  assert.deepStrictEqual(packDirs, []);
  assert.ok(Array.isArray(config.verifyCommands));
});

test('config: 列表拼接 + 项目覆盖标量 + pack 解析', () => {
  const projDir = path.join(TMP, 'proj-pack');
  const packDir = path.join(projDir, '.qgw', 'packs', 'demo');
  fs.mkdirSync(path.join(packDir, 'rules'), { recursive: true });
  fs.writeFileSync(path.join(packDir, 'governance.json'), JSON.stringify({
    promptMessages: [{ pattern: '部署', message: 'pack 提示' }],
  }));
  fs.writeFileSync(path.join(packDir, 'rules', 'demo-rules.json'), JSON.stringify({
    id: 'demo', version: '1.0.0', appliesTo: { extensions: ['.go'] },
    rules: [{ id: 'D-1', severity: 'block', pattern: 'TODO\\(demo\\)', message: 'demo 规则' }],
  }));
  fs.mkdirSync(path.join(projDir, '.qgw'), { recursive: true });
  fs.writeFileSync(path.join(projDir, '.qgw', 'governance.json'), JSON.stringify({
    packs: ['demo'],
    promptMessages: [{ pattern: '发布', message: '项目提示' }],
  }));

  const { loadGovernanceConfig } = require('../hooks/lib/config.js');
  const { config, packDirs } = loadGovernanceConfig(projDir);
  assert.deepStrictEqual(packDirs, [packDir]);
  assert.strictEqual(config.promptMessages.length, 2, 'promptMessages 两层拼接');

  // pack 规则参与引擎
  const { loadRuleSets, matchContent } = require('../hooks/lib/rules.js');
  const sets = loadRuleSets(projDir, packDirs);
  assert.ok(sets.find(s => s.id === 'demo'), 'pack 规则集已加载');
  const vs = matchContent(sets, path.join(projDir, 'm.go'), 'TODO(demo) fix\n');
  assert.ok(vs.find(v => v.sig === 'demo/D-1'));
});

// ─── 4. 事件流：哈希链与夹具排除 ──────────────────────────────────────────
test('event-log: 哈希链 append 后 chainVerify 通过', () => {
  const evolog = require('../scripts/event-log.js');
  const { chainVerify } = require('../scripts/event-query.js');
  evolog.logGateEvent({ result: 'fail', ruleSet: 't', rule: 'R1', sig: 't/R1', file: '/x/a.js', session: 's-test', detail: 'd' });
  evolog.logSummary({ result: 'mixed', passed: [], failed: 1, file: '/x/a.js', track: 'edit', session: 's-test' });
  evolog.logVerifyEvent({ result: 'pass', script: 'verify-x', detail: 'ok', session: 's-test', project: 'p' });
  const r = chainVerify();
  assert.strictEqual(r.broken, 0, `不应有断链（total=${r.total}）`);
  assert.ok(r.total >= 3);
});

test('event-log: 篡改一行后 chainVerify 报告断链', () => {
  const { JSONL_PATH } = require('../scripts/event-log.js');
  const { chainVerify } = require('../scripts/event-query.js');
  const raw = fs.readFileSync(JSONL_PATH, 'utf-8');
  const lines = raw.split('\n').filter(l => l.trim());
  // 篡改倒数第二行的 detail 字段（保留 JSON 合法性，只改内容）
  const tampered = JSON.parse(lines[lines.length - 2]);
  tampered.detail = 'TAMPERED';
  lines[lines.length - 2] = JSON.stringify(tampered);
  fs.writeFileSync(JSONL_PATH, lines.join('\n') + '\n');
  const r = chainVerify();
  assert.strictEqual(r.broken, 1, '篡改后应报告 1 处断链');
  // 还原，避免影响后续测试
  fs.writeFileSync(JSONL_PATH, raw);
  assert.strictEqual(chainVerify().broken, 0);
});

test('event-log: 测试夹具路径不写入生产事件流', () => {
  const evolog = require('../scripts/event-log.js');
  const before = fs.existsSync(evolog.JSONL_PATH)
    ? fs.readFileSync(evolog.JSONL_PATH, 'utf-8') : '';
  evolog.logGateEvent({ result: 'fail', sig: 'x/Y', file: 'C:/p/__test__/f.js', session: 's', detail: 'd' });
  const after = fs.readFileSync(evolog.JSONL_PATH, 'utf-8');
  assert.strictEqual(after, before, '夹具事件不应写入');
});

// ─── 5. 提示限频 ──────────────────────────────────────────────────────────
test('hint-state: 同 key 每会话一次 + 会话封顶', () => {
  const { shouldHint } = require('../hooks/lib/hint-state.js');
  assert.ok(shouldHint('sess-1', 'k', 'file-a', 2), '首次应提示');
  assert.ok(!shouldHint('sess-1', 'k', 'file-a', 2), '同 key 第二次不提示');
  assert.ok(shouldHint('sess-1', 'k', 'file-b', 2), '第二个 key 应提示');
  assert.ok(!shouldHint('sess-1', 'k', 'file-c', 2), '超 cap=2 后不再提示');
  assert.ok(shouldHint('sess-2', 'k', 'file-a', 2), '另一会话重新计数');
});

// ─── 6. 完整性：快照比对 ──────────────────────────────────────────────────
test('integrity: 快照一致 ok / 改动 drift / CRLF 归一 ok / 缺锚 skip', () => {
  const { snapshotTree, checkIntegrity } = require('../hooks/lib/integrity.js');
  const d1 = path.join(TMP, 'i1');
  fs.mkdirSync(path.join(d1, 'hooks'), { recursive: true });
  fs.writeFileSync(path.join(d1, 'hooks', 'a.js'), 'const v = 1;\n');
  const anchorPath = path.join(TMP, 'anchor.json');
  fs.writeFileSync(anchorPath, JSON.stringify(snapshotTree(d1)));

  assert.strictEqual(checkIntegrity({ runtimeDir: d1, anchorPath }).result, 'ok');

  fs.writeFileSync(path.join(d1, 'hooks', 'a.js'), 'const v = 2;\n');
  assert.strictEqual(checkIntegrity({ runtimeDir: d1, anchorPath }).result, 'drift');

  // 仅 CRLF 差异 → ok
  fs.writeFileSync(path.join(d1, 'hooks', 'a.js'), 'const v = 1;\r\n');
  assert.strictEqual(checkIntegrity({ runtimeDir: d1, anchorPath }).result, 'ok');

  assert.strictEqual(
    checkIntegrity({ runtimeDir: d1, anchorPath: path.join(TMP, 'nope.json') }).result,
    'skip-no-anchor');
});

// ─── 7. hook 端到端（子进程，stdin JSON 注入）─────────────────────────────
function runHook(script, stdinObj, extraEnv) {
  return spawnSync('node', [path.join(RUNTIME_ROOT, 'hooks', script)], {
    input: JSON.stringify(stdinObj),
    encoding: 'utf-8',
    timeout: 30000,
    env: Object.assign({}, process.env, extraEnv || {}),
  });
}

test('e2e run-checks: 密钥泄漏文件被 exit 2 阻断', () => {
  const projDir = path.join(TMP, 'e2e-proj');
  fs.mkdirSync(projDir, { recursive: true });
  const badFile = path.join(projDir, 'leak.js');
  fs.writeFileSync(badFile, `const conf = { ${PW}: "hunter2-secret" };\n`);
  const r = runHook('run-checks.js', {
    session_id: 'e2e-1', tool_name: 'Edit',
    tool_input: { file_path: badFile }, cwd: projDir,
  }, { ZCODE_PROJECT_DIR: projDir });
  assert.strictEqual(r.status, 2, `应 exit 2（实际 ${r.status}；stderr=${r.stderr}）`);
  assert.ok(r.stderr.includes('SEC-001'), 'stderr 应含规则编号');
});

test('e2e run-checks: 干净文件放行（exit 0）', () => {
  const projDir = path.join(TMP, 'e2e-proj');
  const okFile = path.join(projDir, 'clean.js');
  fs.writeFileSync(okFile, 'const ok = 1;\n');
  const r = runHook('run-checks.js', {
    session_id: 'e2e-2', tool_name: 'Write',
    tool_input: { file_path: okFile }, cwd: projDir,
  }, { ZCODE_PROJECT_DIR: projDir });
  assert.strictEqual(r.status, 0, `应 exit 0（实际 ${r.status}；stderr=${r.stderr}）`);
});

test('e2e run-checks: verify 审计落 pass 凭证（exitCode 交叉核）', () => {
  const projDir = path.join(TMP, 'e2e-verify');
  fs.mkdirSync(path.join(projDir, '.qgw'), { recursive: true });
  fs.writeFileSync(path.join(projDir, '.qgw', 'governance.json'), JSON.stringify({
    verifyCommands: [{
      name: 'verify-x',
      commandPattern: 'node\\s+\\S*verify-x\\.js',
      passPattern: '=== verify: PASS ===',
      failPattern: '=== verify: FAIL ===',
    }],
  }));
  const r = runHook('run-checks.js', {
    session_id: 'e2e-3', tool_name: 'Bash',
    tool_input: { command: 'node scripts/verify-x.js --all', },
    tool_response: { stdout: 'step1 ok\n=== verify: PASS ===', stderr: '', exitCode: 0 },
    cwd: projDir,
  }, { ZCODE_PROJECT_DIR: projDir });
  assert.strictEqual(r.status, 0);
  const { readEvents } = require('../scripts/event-query.js');
  const vers = readEvents().filter(e => e.type === 'verify' && e.session === 'e2e-3');
  assert.strictEqual(vers.length, 1, '应落一条 verify 事件');
  assert.strictEqual(vers[0].result, 'pass');
});

test('e2e run-checks: 结论行与退出码矛盾不采信', () => {
  const projDir = path.join(TMP, 'e2e-verify');
  runHook('run-checks.js', {
    session_id: 'e2e-4', tool_name: 'Bash',
    tool_input: { command: 'node verify-x.js' },
    tool_response: { stdout: '=== verify: PASS ===', stderr: '', exitCode: 1 },
    cwd: projDir,
  }, { ZCODE_PROJECT_DIR: projDir });
  const { readEvents } = require('../scripts/event-query.js');
  const vers = readEvents().filter(e => e.type === 'verify' && e.session === 'e2e-4');
  assert.strictEqual(vers[0].result, 'unknown', '矛盾凭证应为 unknown');
});

test('e2e turn-stats: 无事件静默 exit 0 且 stdout 为空', () => {
  const r = runHook('turn-stats.js', { session_id: 'no-such-session' });
  assert.strictEqual(r.status, 0);
  assert.strictEqual(r.stdout, '', 'stdout 必须为空（防 Stop 死循环）');
});

test('e2e prompt-inject: 未配置关键词时零输出', () => {
  const projDir = path.join(TMP, 'e2e-proj');  // 无 .qgw 配置
  const r = runHook('prompt-inject.js', { session_id: 'e2e-5', prompt: '随便聊聊' },
    { ZCODE_PROJECT_DIR: projDir });
  assert.strictEqual(r.status, 0);
  assert.strictEqual(r.stdout, '', '默认配置下不应有任何注入');
});

// ─── 汇总 ─────────────────────────────────────────────────────────────────
const failed = results.filter(r => !r.ok);
console.log(`\n${failed.length === 0 ? 'ALL PASS' : `SOME FAIL (${failed.length})`}（共 ${results.length} 项）`);
fs.rmSync(TMP, { recursive: true, force: true });
process.exit(failed.length === 0 ? 0 : 1);
