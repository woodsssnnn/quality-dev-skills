#!/usr/bin/env node
/**
 * run-checks.js — PostToolUse 门禁入口（governance 运行时）
 *
 * 作用：把宿主的 Edit/Write 事件桥接到声明式规则引擎。
 *       stdin 收 PostToolUse JSON → 取 file_path → 按规则集匹配 →
 *       命中 block 级违规用 exit 2 把错误喂回 agent，强制它继续修复。
 *
 * 这是把"死的 pre-commit"升级为"活的 PostToolUse 门禁"的关键一环：
 * agent 改文件不触发 git commit，pre-commit 永远不会跑；本 hook 在
 * 每次写入后立即触发，是真正能拦住违规的时点。
 *
 * 工具分流：
 *   Bash  → 验证运行审计（DoD 机器凭证）+ 可配置的 Bash 命令提示
 *   Read  → 轻量记录（track=read，供轮统计）
 *   Edit/Write → 规则引擎门禁（block 违规 exit 2；warn 违规/hint 提示
 *                以 additionalContext 注入，非阻断）
 *
 * 退出码（PostToolUse 协议）：
 *   0 = 通过（stdout 进 transcript）
 *   2 = 阻断（stderr 喂回 agent，强制它继续修）← block 级违规用这个
 *   其他 = 非阻断错误（不打断 agent）
 *
 * 纪律：门禁自身任何异常都不得阻断 agent——所有内部失败静默/仅留
 * 可观测信号后 exit 0。配置与规则集全部数据驱动（三层发现，见 lib/config.js
 * 与 lib/rules.js），本文件不含任何领域假设。
 *
 * 依赖：Node.js >= 12（仅标准库）。
 */

const fs = require('fs');
const path = require('path');
const { normalizeHookInput } = require('./lib/hook-input.js');
const { loadGovernanceConfig } = require('./lib/config.js');
const { loadRuleSets, matchContent, runScriptRules } = require('./lib/rules.js');
const { shouldHint } = require('./lib/hint-state.js');
const evolog = require('../scripts/event-log.js');
const { buildRepeatHint } = require('../scripts/event-query.js');

// 判断 stdin 读取异常是否是"预期的非 hook 调用"（fd 0 不可读）：
// EAGAIN/EOF/管道关闭——手动测试、非 hook 调用场景，静默放过
function isExpectedNoStdin(e) {
  const code = e.code || '';
  return code === 'EAGAIN' || code === 'EOF' || /read EIO|end-off-file/i.test(e.message || '');
}

let raw = '';
try {
  raw = fs.readFileSync(0, 'utf-8');
} catch (e) {
  if (!isExpectedNoStdin(e)) {
    console.error(`[governance hook] stdin 读取异常（非预期），放行但请检查：${e.code || e.message}`);
  }
  process.exit(0);
}

let input;
try {
  input = JSON.parse(raw);
} catch (e) {
  // JSON 解析失败 → 静默放行，绝不因自身 bug 阻断 agent
  process.exit(0);
}
input = normalizeHookInput(input);

const toolName = input.tool_name || '';
const toolInput = input.tool_input || {};
const filePath = toolInput.file_path || toolInput.path;
const sessionId = input.session_id || process.env.CLAUDE_SESSION_ID || '';
const projectDir = process.env.ZCODE_PROJECT_DIR || process.env.CLAUDE_PROJECT_DIR || input.cwd || '';

function loadCtx() {
  const { config, packDirs } = loadGovernanceConfig(projectDir);
  const ruleSets = loadRuleSets(projectDir, packDirs);
  return { config, ruleSets };
}

// ─── Bash 分支：验证运行审计 + 可配置命令提示 ─────────────────────────────
if (/^Bash$/i.test(toolName)) {
  const bashCommand = toolInput.command || '';
  try {
    // 验证审计：命令须锚定配置的验证命令模式（防 grep/cat 碰巧带脚本名
    // 铸假凭证）；结论行须与 exitCode 交叉核（矛盾不采信）；解析不出
    // 结论照记 result:'unknown'（"没找到结论"≠"通过"）。
    for (const vc of (loadCtx().config.verifyCommands || [])) {
      let cmdRe;
      try { cmdRe = new RegExp(vc.commandPattern); } catch (e) { continue; }
      if (!cmdRe.test(bashCommand)) continue;

      let passRe = null, failRe = null;
      try {
        passRe = vc.passPattern ? new RegExp(vc.passPattern) : null;
        failRe = vc.failPattern ? new RegExp(vc.failPattern) : null;
      } catch (e) { /* 坏模式按 unknown 记 */ }

      const tr = (typeof (input.tool_response || input.toolResponse) === 'object')
        ? (input.tool_response || input.toolResponse) : {};
      const out = `${tr.stdout || ''}\n${tr.stderr || ''}`;
      const exitCode = tr.exitCode;
      let result = 'unknown';
      let detail = `exitCode=${exitCode}`;
      if (passRe && passRe.test(out) && exitCode !== 0) {
        detail = `结论行与退出码矛盾（exitCode=${exitCode}），不采信`;
      } else if (passRe && passRe.test(out)) {
        result = 'pass';
        detail = `pass | exitCode=${exitCode}`;
      } else if (failRe && failRe.test(out)) {
        result = 'fail';
        detail = `fail | exitCode=${exitCode}`;
      } else if (tr.timedOut) {
        result = 'fail';
        detail = `timedOut | exitCode=${exitCode}`;
      }
      evolog.logVerifyEvent({
        result,
        script: vc.name || 'verify',
        detail,
        session: sessionId,
        project: path.basename(projectDir || process.cwd()),
      });
    }

    // 可配置的 Bash 命令提示（additionalContext，非阻断，限频）
    const hints = [];
    for (const h of (loadCtx().config.bashHints || [])) {
      let re;
      try { re = new RegExp(h.pattern); } catch (e) { continue; }
      if (!re.test(bashCommand)) continue;
      if (!shouldHint(sessionId, `bash:${h.id || h.pattern}`, '*', h.cap || 1)) continue;
      hints.push(h.message);
      evolog.logHintEvent({ kind: `bash:${h.id || h.pattern}`, message: h.message, session: sessionId });
    }
    if (hints.length) process.stdout.write(JSON.stringify({ additionalContext: hints.join('\n') }));
  } catch (e) {
    console.error('[governance] Bash 分支异常（已放行）: ' + e.message);
  }
  process.exit(0);
}

// ─── Read 分支：轻量记录（供轮统计，不跑校验）──────────────────────────────
if (/^Read$/i.test(toolName)) {
  if (!filePath || !fs.existsSync(filePath)) process.exit(0);
  try {
    evolog.logSummary({ result: 'pass', passed: [], failed: 0, file: filePath, track: 'read', session: sessionId });
  } catch (e) { /* 记录失败不阻断 */ }
  process.exit(0);
}

// 非 Edit/Write 不处理
if (!/^(Edit|Write)$/i.test(toolName)) process.exit(0);

// 取不到路径或文件不存在 → 放行
if (!filePath || !fs.existsSync(filePath)) process.exit(0);

// ─── Edit/Write 主门禁：声明式规则引擎 ─────────────────────────────────────
try {
  const { config, ruleSets } = loadCtx();

  let content = '';
  try {
    content = fs.readFileSync(filePath, 'utf-8');
  } catch (e) {
    process.exit(0);  // 读不了内容（二进制/编码异常）→ 放行
  }

  const violations = matchContent(ruleSets, filePath, content).concat(runScriptRules(ruleSets, filePath));
  const blockViolations = violations.filter(v => v.severity === 'block');
  const warnViolations = violations.filter(v => v.severity === 'warn');

  // ─── 无 block 违规：warn 提示 + 可配置 hint 注入（additionalContext）───
  if (blockViolations.length === 0) {
    const parts = [];

    for (const w of warnViolations) {
      // warn 级违规提示：同文件每会话一次（避免刷屏）
      if (shouldHint(sessionId, `warn:${w.sig}`, filePath, 1)) {
        parts.push(`[governance 提醒] ${w.sig}: ${w.message}（第 ${w.line} 行附近）`);
      }
    }
    for (const h of (config.hints || [])) {
      if (!h.id || !h.message) continue;
      // hint 可按扩展名/文件名正则收窄适用范围
      if (h.extensions) {
        const ext = path.extname(filePath).toLowerCase();
        if (!h.extensions.map(x => x.toLowerCase()).includes(ext)) continue;
      }
      if (h.filenamePattern) {
        try {
          if (!new RegExp(h.filenamePattern).test(path.basename(filePath))) continue;
        } catch (e) { continue; }
      }
      if (!shouldHint(sessionId, `hint:${h.id}`, filePath, h.cap || 3)) continue;
      parts.push(h.message);
      evolog.logHintEvent({ kind: `hint:${h.id}`, message: h.message, file: filePath, session: sessionId });
    }

    evolog.logSummary({
      result: warnViolations.length ? 'warn-only' : 'pass',
      passed: [], failed: 0, warned: warnViolations.length,
      file: filePath, track: 'edit', session: sessionId,
    });
    if (parts.length) process.stdout.write(JSON.stringify({ additionalContext: parts.join('\n') }));
    process.exit(0);
  }

  // ─── block 违规：记事件 → stderr + exit 2 强制 agent 继续修 ────────────
  const failSigs = [...new Set(blockViolations.map(v => v.sig))];
  for (const v of blockViolations) {
    evolog.logGateEvent({
      result: 'fail', ruleSet: v.ruleSet, rule: v.rule, sig: v.sig,
      file: filePath, session: sessionId,
      detail: `L${v.line}: ${v.excerpt}`,
    });
  }
  evolog.logSummary({
    result: 'mixed', passed: [], failed: failSigs.length, warned: warnViolations.length,
    file: filePath, track: 'edit', session: sessionId,
  });

  const msg = blockViolations
    .map(v => `[governance 门禁] ${v.sig} 命中违规，必须修复后继续：\n  L${v.line}: ${v.excerpt}\n  ${v.message}`)
    .join('\n\n');
  let evoHint = '';
  try {
    evoHint = buildRepeatHint(failSigs);
  } catch (e) { /* 提示构建失败不影响阻断 */ }
  console.error(evoHint ? msg + '\n\n' + evoHint : msg);
  process.exit(2);
} catch (e) {
  // 门禁自身异常：留可观测信号，但绝不阻断 agent
  console.error('[governance] 门禁引擎异常（已放行，请检查规则集配置）: ' + e.message);
  process.exit(0);
}
