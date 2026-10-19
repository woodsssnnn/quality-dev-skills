/**
 * config.js — 治理配置的发现与合并（运行时零领域假设的核心）
 *
 * 配置三层，优先级从低到高：
 *   1. 内置默认   governance/config.default.json（全部为空/中立值）
 *   2. 领域包     项目配置声明 packs: ["<name>"]，按顺序在
 *                 <projectDir>/.qgw/packs/<name>/ 与 <repoRoot>/domains/<name>/
 *                 两处解析（前者存在则优先——项目可私有覆写同名包）
 *   3. 项目本地   <projectDir>/.qgw/governance.json
 *
 * 合并规则：标量/对象取高优先级覆盖；列表类（promptMessages / verifyCommands /
 * bashHints / hints）逐层拼接（低层在前），让每层只增量贡献自己的条目。
 */

const fs = require('fs');
const path = require('path');

const RUNTIME_ROOT = path.resolve(__dirname, '..', '..');
const DEFAULT_CONFIG_PATH = path.join(RUNTIME_ROOT, 'config.default.json');

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf-8'));
}

function existsDir(dir) {
  try {
    return fs.statSync(dir).isDirectory();
  } catch (e) {
    return false;
  }
}

/**
 * 解析一个领域包的目录：项目私有目录优先，其次本仓库 domains/<name>。
 * 都不存在返回 null。
 */
function resolvePackDir(projectDir, name) {
  const candidates = [
    projectDir ? path.join(projectDir, '.qgw', 'packs', name) : null,
    path.join(RUNTIME_ROOT, '..', 'domains', name),
  ].filter(Boolean);
  for (const c of candidates) {
    if (existsDir(c)) return c;
  }
  return null;
}

const LIST_KEYS = ['promptMessages', 'verifyCommands', 'bashHints', 'hints'];

function mergeConfigs(layers) {
  // layers: 低优先级在前
  const merged = {};
  for (const layer of layers) {
    if (!layer) continue;
    for (const [k, v] of Object.entries(layer)) {
      if (LIST_KEYS.includes(k) && Array.isArray(v)) {
        merged[k] = (merged[k] || []).concat(v);
      } else {
        merged[k] = v;
      }
    }
  }
  return merged;
}

/**
 * 加载合并后的治理配置。
 * @param {string} projectDir 项目根目录（可为空——纯内置模式）
 * @returns {{ config: object, packDirs: string[], sources: string[] }}
 */
function loadGovernanceConfig(projectDir) {
  const sources = [];
  const layers = [];

  // 1. 内置默认
  let defaults = {};
  try {
    defaults = readJson(DEFAULT_CONFIG_PATH);
    sources.push('builtin');
  } catch (e) { /* 默认配置缺失时按空配置运行，规则引擎只跑内置规则集 */ }
  layers.push(defaults);

  // 2. 项目本地配置（同时声明 packs）
  let projectConfig = null;
  if (projectDir) {
    const p = path.join(projectDir, '.qgw', 'governance.json');
    if (fs.existsSync(p)) {
      try {
        projectConfig = readJson(p);
        sources.push('project');
      } catch (e) {
        console.error(`[governance] 项目配置解析失败（按无项目配置继续）: ${p}`);
      }
    }
  }

  // 3. 领域包（按声明顺序，后声明的覆盖先声明的）
  const packDirs = [];
  const packNames = (projectConfig && Array.isArray(projectConfig.packs)) ? projectConfig.packs : [];
  for (const name of packNames) {
    const dir = resolvePackDir(projectDir, name);
    if (!dir) {
      console.error(`[governance] 领域包不存在（已跳过）: ${name}`);
      continue;
    }
    const cfgPath = path.join(dir, 'governance.json');
    if (fs.existsSync(cfgPath)) {
      try {
        layers.push(readJson(cfgPath));
        sources.push(`pack:${name}`);
      } catch (e) {
        console.error(`[governance] 领域包配置解析失败（已跳过）: ${cfgPath}`);
      }
    }
    packDirs.push(dir);
  }

  // 4. 项目配置最后合入（最高优先级）
  if (projectConfig) layers.push(projectConfig);

  const config = mergeConfigs(layers);
  return { config, packDirs, sources };
}

module.exports = { loadGovernanceConfig, resolvePackDir, RUNTIME_ROOT };
