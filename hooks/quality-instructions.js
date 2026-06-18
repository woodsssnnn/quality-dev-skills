#!/usr/bin/env node
// quality-dev-skills — 共享指令构建器
//
// 所有平台共享同一个指令构建逻辑。
// 根据模式过滤和格式化指令。

const fs = require('fs');
const path = require('path');

const DEFAULT_MODE = 'full';
const VALID_MODES = ['lite', 'full', 'ultra', 'off'];

const SKILL_PATH = path.join(__dirname, '..', 'skills', 'quality-gate-workflow', 'SKILL.md');

function normalizeMode(mode) {
  if (!mode) return DEFAULT_MODE;
  const normalized = mode.toLowerCase().trim();
  return VALID_MODES.includes(normalized) ? normalized : DEFAULT_MODE;
}

function normalizePersistedMode(mode) {
  if (!mode) return null;
  const normalized = mode.toLowerCase().trim();
  return VALID_MODES.includes(normalized) ? normalized : null;
}

function filterSkillBodyForMode(body, mode) {
  const effectiveMode = normalizeMode(mode);
  const withoutFrontmatter = String(body || '').replace(/^---[\s\S]*?---\s*/, '');

  // 根据模式过滤内容
  // lite: 只保留核心规则
  // full: 保留所有规则
  // ultra: 保留所有规则 + 严格检查
  // off: 不保留任何规则

  if (effectiveMode === 'off') {
    return '';
  }

  if (effectiveMode === 'lite') {
    // lite模式只保留核心规则
    return withoutFrontmatter
      .split(/\r?\n/)
      .filter((line) => {
        // 保留标题和核心规则
        return line.match(/^#/) || 
               line.match(/^\*\*/) || 
               line.match(/^-\s/) ||
               line.trim() === '';
      })
      .join('\n');
  }

  // full和ultra模式保留所有规则
  return withoutFrontmatter;
}

function getFallbackInstructions(mode) {
  const effectiveMode = normalizeMode(mode);
  
  return `QUALITY DEV SKILLS MODE ACTIVE — level: ${effectiveMode}

# 质量门禁工作流

## 快速开始

1. 安装技能：在项目目录执行 \`bash scripts/install.sh\`
2. 初始化工作区：\`bash scripts/health-check.sh --init-workspace\`
3. 选择触发参数：\`--gate1\`（需求→Plan）/ \`--gate2\`（Plan→代码）/ \`--all\`（全流程）

## 核心机制

- **五层防线**：提取验收标准 → PM顾问评议 → 写plan → 架构师顾问评议 → 自验 → 独立verifier子代理
- **角色分工**：顾问判断"合不合理"，verifier判断"对不对齐"
- **根因分类**：CODE（代码偏差）/ PLAN（计划偏差）
- **100% 通过才放行**

## 参数调用语法

| 参数 | 含义 |
|------|------|
| \`--gate1\` | Gate 1: 需求→Plan |
| \`--gate2\` | Gate 2: Plan→代码 |
| \`--all\` | 全流程 Gate 1+2 串行 |
| \`--self\` | 自检：复盘指定会话的Gate执行质量 |

## 强度级别

| 级别 | 说明 |
|------|------|
| **lite** | 基础规范，适合快速开发 |
| **full** | 完整规范，适合生产环境（默认） |
| **ultra** | 严格规范，适合关键系统 |
| **off** | 关闭规范检查 |

当前级别: **${effectiveMode}**。切换: \`/quality-dev-skills lite|full|ultra|off\`

## YAGNI 检查

在编写代码前，必须通过 YAGNI 梯队检查：

1. 这个功能需要存在吗？→ 不需要：跳过（YAGNI）
2. 标准库能做吗？→ 用它
3. 原生平台特性？→ 用它
4. 已安装的依赖？→ 用它
5. 能一行搞定吗？→ 一行
6. 只有那时：写最小可工作代码`;
}

function getQualityGateInstructions(mode) {
  const configuredMode = normalizePersistedMode(mode) || DEFAULT_MODE;

  if (configuredMode === 'off') {
    return '';
  }

  const effectiveMode = normalizeMode(configuredMode);

  try {
    return `QUALITY DEV SKILLS MODE ACTIVE — level: ${effectiveMode}\n\n` +
      filterSkillBodyForMode(fs.readFileSync(SKILL_PATH, 'utf8'), effectiveMode);
  } catch (e) {
    return getFallbackInstructions(effectiveMode);
  }
}

module.exports = {
  normalizeMode,
  normalizePersistedMode,
  filterSkillBodyForMode,
  getFallbackInstructions,
  getQualityGateInstructions,
  DEFAULT_MODE,
  VALID_MODES,
};
