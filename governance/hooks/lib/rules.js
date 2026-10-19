/**
 * rules.js — 声明式规则集的发现、加载与匹配（门禁引擎核心）
 *
 * 规则集是数据文件（JSON），贡献者不改引擎即可新增门禁规则。
 * 发现顺序（同 id 规则集后者覆盖前者）：
 *   1. governance/rules/builtin/*.json        内置中立规则
 *   2. <packDir>/rules/*.json                 领域包规则（按 pack 声明顺序）
 *   3. <projectDir>/.qgw/rules/*.json         项目本地规则（最高优先）
 *
 * 规则集 schema（详见 governance/README.md）：
 *   {
 *     "id": "secret-leaks", "version": "1.0.0",
 *     "appliesTo": { "extensions": [".js"] },
 *     "rules": [
 *       { "id": "SEC-001", "severity": "block"|"warn",
 *         "pattern": "<js regex>", "flags": "i",
 *         "message": "命中时展示给 agent 的说明",
 *         "script": "check-xxx.js" }   ← 脚本逃生舱，二选一
 *     ]
 *   }
 *
 * 脚本规则约定：以 `node <script> <filePath>` 运行（script 相对规则集目录），
 *   退出码 0=通过，非 0=违规（stdout 即违规说明，可含 [SIG] 签名行）。
 * 引擎自身异常一律视为"该条规则不命中"——门禁自身的故障不能误伤 agent。
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const RUNTIME_ROOT = path.resolve(__dirname, '..', '..');
const BUILTIN_RULES_DIR = path.join(RUNTIME_ROOT, 'rules', 'builtin');

function listJsonFiles(dir) {
  try {
    return fs.readdirSync(dir)
      .filter(f => f.endsWith('.json'))
      .map(f => path.join(dir, f));
  } catch (e) {
    return [];
  }
}

function loadRuleSetFile(file) {
  try {
    const set = JSON.parse(fs.readFileSync(file, 'utf-8'));
    if (!set.id || !Array.isArray(set.rules)) return null;
    set.sourceDir = path.dirname(file);
    set.sourceFile = file;
    return set;
  } catch (e) {
    console.error(`[governance] 规则集解析失败（已跳过）: ${file}: ${e.message}`);
    return null;
  }
}

/**
 * 按三层顺序加载全部规则集（同 id 后加载的覆盖先加载的）。
 * @param {string} projectDir 项目根目录（可为空）
 * @param {string[]} packDirs 领域包目录列表（来自 config.js）
 */
function loadRuleSets(projectDir, packDirs) {
  const byId = new Map();
  const dirs = [BUILTIN_RULES_DIR];
  for (const d of packDirs || []) dirs.push(path.join(d, 'rules'));
  if (projectDir) dirs.push(path.join(projectDir, '.qgw', 'rules'));

  for (const dir of dirs) {
    for (const file of listJsonFiles(dir)) {
      const set = loadRuleSetFile(file);
      if (set) byId.set(set.id, set);
    }
  }
  return [...byId.values()];
}

function appliesTo(set, ext) {
  const exts = (set.appliesTo && set.appliesTo.extensions) || [];
  return exts.map(e => e.toLowerCase()).includes(ext);
}

/** 编译并缓存规则正则；非法正则的规则跳过（不阻断其余规则）。 */
function ruleRegex(rule) {
  if (!rule.pattern) return null;
  if (rule._re) return rule._re;
  try {
    rule._re = new RegExp(rule.pattern, rule.flags || '');
    return rule._re;
  } catch (e) {
    console.error(`[governance] 规则正则非法（已跳过）: ${rule.id}: ${e.message}`);
    rule._re = false;
    return null;
  }
}

/**
 * 对文件内容执行声明式匹配。
 * @returns {Array<{ruleSet: string, rule: string, severity: string, line: number,
 *            excerpt: string, message: string, sig: string}>}
 */
function matchContent(ruleSets, filePath, content) {
  const ext = path.extname(filePath).toLowerCase();
  const lines = content.split(/\r?\n/);
  const violations = [];
  for (const set of ruleSets) {
    if (!appliesTo(set, ext)) continue;
    for (const rule of set.rules) {
      if (!rule.id) continue;
      const re = ruleRegex(rule);
      if (!re) continue;
      for (let i = 0; i < lines.length; i++) {
        if (re.test(lines[i])) {
          violations.push({
            ruleSet: set.id,
            rule: rule.id,
            severity: rule.severity === 'warn' ? 'warn' : 'block',
            line: i + 1,
            excerpt: lines[i].trim().slice(0, 160),
            message: rule.message || `命中规则 ${set.id}/${rule.id}`,
            sig: `${set.id}/${rule.id}`,
          });
          break;  // 同一规则命中一次即算，避免同规则刷屏
        }
      }
    }
  }
  return violations;
}

/**
 * 执行脚本逃生舱规则（规则声明了 script 字段）。
 * 返回 violations（同 matchContent 结构，line/excerpt 由脚本输出承载）。
 */
function runScriptRules(ruleSets, filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const violations = [];
  for (const set of ruleSets) {
    if (!appliesTo(set, ext)) continue;
    for (const rule of set.rules) {
      if (!rule.id || !rule.script) continue;
      const scriptPath = path.join(set.sourceDir, rule.script);
      if (!fs.existsSync(scriptPath)) continue;
      const r = spawnSync('node', [scriptPath, filePath], {
        encoding: 'utf-8',
        timeout: 20000,
        cwd: set.sourceDir,
      });
      // spawn 失败/超时（status === null）不能当违规——会误判 + 写脏数据
      if (r.status === null || r.status === 0) continue;
      const out = ((r.stdout || '') + (r.stderr || '')).trim();
      violations.push({
        ruleSet: set.id,
        rule: rule.id,
        severity: rule.severity === 'warn' ? 'warn' : 'block',
        line: 0,
        excerpt: out.split(/\r?\n/).slice(0, 6).join('\n'),
        message: rule.message || `命中规则 ${set.id}/${rule.id}`,
        sig: `${set.id}/${rule.id}`,
      });
    }
  }
  return violations;
}

module.exports = { loadRuleSets, matchContent, runScriptRules, BUILTIN_RULES_DIR };
