#!/usr/bin/env node
/**
 * install-hooks.js — 把 governance 运行时装配进目标项目（幂等）
 *
 * 用法（在目标项目根目录下执行）：
 *   cd <project-root>
 *   node <governance路径>/scripts/install-hooks.js            # 装配
 *   node <governance路径>/scripts/install-hooks.js --remove   # 移除装配
 *
 * 脚本只作用于当前工作目录（不接收路径参数，从根上避免越权写入）。
 *
 * 行为：
 *   1. 在项目 .zcode/settings.json 的 hooks 段写入 4 个 hook 入口
 *      （"<node 绝对路径>" "<运行时>/hooks/<script>.js"，跨平台无需 .cmd）
 *   2. 保留项目已有的其他 hooks 条目；重复执行只替换自身条目（幂等）
 *   3. 对运行时目录写完整性锚清单（SessionStart integrity 比对基准）
 *
 * 装配后建议（可选）：在项目 .qgw/governance.json 声明领域包/提示/验证
 * 命令模式（见 governance/README.md），否则运行时仅启用内置中立规则。
 *
 * 依赖：仅 Node 标准库。
 */

const fs = require('fs');
const path = require('path');
const { snapshotTree } = require('../hooks/lib/integrity.js');
const { getDataHome } = require('../hooks/lib/data-home.js');

const RUNTIME_ROOT = path.resolve(__dirname, '..');
const MARKER = path.join('governance', 'hooks').replace(/\\/g, '/');
const projectDir = process.cwd();
const settingsPath = path.join(projectDir, '.zcode', 'settings.json');

const remove = process.argv.includes('--remove');

const HOOK_DEFS = [
  { event: 'SessionStart', matcher: null, script: 'integrity-check.js', timeout: 10 },
  { event: 'PostToolUse', matcher: 'Edit|Write|Bash|Read', script: 'run-checks.js', timeout: 30 },
  { event: 'UserPromptSubmit', matcher: '.*', script: 'prompt-inject.js', timeout: 10 },
  { event: 'Stop', matcher: null, script: 'turn-stats.js', timeout: 10 },
];

function readJson(file, fallback) {
  try {
    return JSON.parse(fs.readFileSync(file, 'utf-8'));
  } catch (e) {
    return fallback;
  }
}

/** 条目是否属于本运行时（幂等替换/移除的判定依据） */
function isOurs(hookCmd) {
  return typeof hookCmd === 'string' && hookCmd.replace(/\\/g, '/').includes(MARKER);
}

function commandFor(script) {
  return `"${process.execPath}" "${path.join(RUNTIME_ROOT, 'hooks', script)}"`;
}

function applyHooks(settings, defs, removeMode) {
  const hooks = settings.hooks || (settings.hooks = {});
  for (const def of defs) {
    const groups = Array.isArray(hooks[def.event]) ? hooks[def.event] : [];
    // 移除/替换：剔除本运行时的旧条目组；纯项目条目一律保留
    const kept = groups.filter(g => {
      const cmds = ((g && g.hooks) || []).map(h => h && h.command);
      const oursCount = cmds.filter(isOurs).length;
      if (oursCount === 0) return true;          // 纯项目条目，保留
      return cmds.length !== oursCount;          // 混合组：仅当含非 ours 时保留（罕见）
    });
    if (removeMode) {
      hooks[def.event] = kept;
      continue;
    }
    hooks[def.event] = kept.concat([{
      ...(def.matcher ? { matcher: def.matcher } : {}),
      hooks: [{ type: 'command', command: commandFor(def.script), timeout: def.timeout }],
    }]);
  }
  // 清理空数组键
  for (const k of Object.keys(hooks)) {
    if (Array.isArray(hooks[k]) && hooks[k].length === 0) delete hooks[k];
  }
}

// ─── 主流程 ───────────────────────────────────────────────────────────────
// 项目目录固定为 process.cwd()（不收路径参数），写入目标从根上不受
// 不可信输入影响；本项目内路径均为拼接常量。
const settings = readJson(settingsPath, {});
applyHooks(settings, HOOK_DEFS, remove);

fs.mkdirSync(path.dirname(settingsPath), { recursive: true });
fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + '\n');

if (remove) {
  console.log(`✅ 已从 ${settingsPath} 移除 governance hooks（项目其他 hooks 保留）`);
  process.exit(0);
}

// 写完整性锚清单（SessionStart integrity 比对基准；重装/更新运行时后需重跑）
const anchorPath = path.join(getDataHome(), 'integrity-anchor.json');
const snap = snapshotTree(RUNTIME_ROOT);
fs.writeFileSync(anchorPath, JSON.stringify(snap, null, 2));

console.log(`✅ governance hooks 已装配到 ${settingsPath}`);
console.log(`✅ 完整性锚清单已更新（${Object.keys(snap.files).length} 文件）: ${anchorPath}`);
console.log('');
console.log('后续（可选）：');
console.log('  1. 项目 .qgw/governance.json —— 声明 packs / 提示 / 验证命令模式');
console.log('  2. 项目 .qgw/rules/*.json —— 项目本地规则集（最高优先）');
console.log('  3. 事件流查询：node governance/scripts/event-query.js --tail');
