---
name: qgw-init
description: |-
  Use when initializing QGW workspace for a new project.
  Triggers on: --init, "初始化 QGW", "initialize QGW", "setup QGW", "setup quality gate".
  Guides through platform selection, workflow mode, directory creation, and health check.
allowed-tools:
  - Task
  - Agent
  - Read
  - Grep
  - Glob
  - Bash(mkdir *)
  - Bash(python *)
  - Bash(bash *)
  - Bash(cat *)
metadata:
  version: 0.8.0.0
---

# QGW Init — 项目初始化向导

> 7 步交互式引导，为新项目完成 QGW 质量门禁的全套初始化配置。

---

## 触发方式

| 方式 | 示例 |
|------|------|
| 参数 | `--init` |
| 关键词 | "初始化 QGW"、"initialize QGW"、"setup QGW"、"setup quality gate" |

---

## 初始化流程（7 步）

### Step 1: 环境检测

自动检测当前项目环境，输出检测报告：

```
检测项:
  ✅ / ❌ AI 平台（Claude Code / Codex / OpenCode / MiMoCode / 其他）
  ✅ / ❌ Python 3（python3 或 python）
  ✅ / ❌ Git 仓库（.git/ 目录）
  ✅ / ❌ 已有 .qgw/ 目录（如存在则询问是否覆盖）
  ✅ / ❌ 已有 docs/ 产出物目录
```

**规则**：
- Python 缺失 → 警告：部分功能（gate-enforcer、health-check 详细模式）将不可用
- Git 缺失 → 警告：Hook 功能不可用，但初始化仍可继续
- 已有 `.qgw/` → 提示用户选择：覆盖 / 合并 / 取消

### Step 2: 平台适配器选择

自动检测当前 AI 平台，并请用户确认：

| 平台 | 标识 | 配置文件 |
|------|------|----------|
| Claude Code | `claude` | `.claude/settings.local.json` |
| Codex | `codex` | `AGENTS.md` |
| OpenCode | `opencode` | `plugin.mjs` |
| MiMoCode | `mimo` | `plugin.json` |
| General | `general` | `AGENTS.md` |

**自动检测规则**：
1. 存在 `.claude/` 目录 → 建议 Claude Code
2. 存在 `AGENTS.md` 且含 "codex" 关键词 → 建议 Codex
3. 存在 `opencode.config.*` → 建议 OpenCode
4. 存在 `.mimo/` 目录 → 建议 MiMoCode
5. 以上均无 → 建议 General

用户可覆盖自动检测结果。选择后加载对应平台配置模板 → 详见 [references/platform-configs.md](references/platform-configs.md)。

### Step 3: 工作流模式选择

提供三种模式供选择：

| 模式 | 参数 | 适用场景 |
|------|------|----------|
| **lite** | `--lite` | 单文件改动、快速修 Bug、跳过顾问步骤 |
| **full** | （默认） | 标准功能开发，所有步骤完整执行 |
| **ultra** | `--strict --e2e` | 关键系统、零容忍、端到端验证 |

详细模式差异 → 详见 [references/workflow-modes.md](references/workflow-modes.md)。

### Step 4: `.qgw/` 目录创建

在项目根目录创建 `.qgw/` 配置目录：

```
.qgw/
├── config.json          # 项目 QGW 配置（platform, mode, engine）
├── constitution.md      # 项目 constitution（需求解析约束）
└── docs/                # 项目级文档覆盖
```

**config.json 模板**：

```json
{
  "platform": "<selected-platform>",
  "mode": "<selected-mode>",
  "language": "zh",
  "hooks": { "mode": "strict" },
  "engine": {
    "enabled": true,
    "strict_mode": true,
    "state_file": "docs/.qgw-engine-state.json",
    "checkpoint_dir": "docs/.qgw-checkpoints"
  },
  "initialized": "<ISO-8601 timestamp>",
  "version": "0.8.0.0"
}
```

**constitution.md 模板**：

```markdown
# 项目 Constitution

## 需求解析约束

<!-- 在此定义项目特有的需求解析规则 -->

- 所有需求必须明确标注优先级（P0/P1/P2）
- 功能性需求必须包含验收标准
- 非功能性需求必须量化指标
```

### Step 5: PRD 目录结构创建（可选）

询问用户是否需要创建 PRD 目录：

```
docs/prd/<feature-name>/
├── prd.md               # 产品需求文档
├── plan.md              # 实现计划（Gate 1 产出）
└── verification/        # 验收数据
```

如用户指定 `--with-prd <name>`，自动创建；否则跳过此步。

### Step 6: 平台配置写入

根据 Step 2 选择的平台，写入对应配置：

**Claude Code**：
- 写入 `.claude/settings.local.json`（Hook 配置 + 环境变量）

**Codex / General**：
- 写入或更新 `AGENTS.md`（QGW 触发词 + 配置声明）

**OpenCode**：
- 写入 `plugin.mjs`（QGW 插件配置）

**MiMoCode**：
- 写入 `plugin.json`（QGW 插件配置）

具体配置内容 → 详见 [references/platform-configs.md](references/platform-configs.md)。

### Step 7: 健康检查验证

运行 health-check 验证初始化结果：

```bash
bash <skill-dir>/../quality-gate-workflow/scripts/health-check.sh --init-workspace
```

检查项：
- `.qgw/config.json` 格式有效
- `docs/` 子目录已创建（plans / verification / reports / sessions）
- 平台配置文件已写入
- 如选择了 PRD，PRD 目录已创建

输出初始化摘要：

```
=========================================
 QGW 初始化完成
=========================================
  平台:     claude-code
  模式:     full
  PRD:      未创建
  目录:     .qgw/ ✅  docs/plans/ ✅  docs/verification/ ✅
            docs/reports/ ✅  docs/sessions/ ✅
  配置:     .claude/settings.local.json ✅
=========================================
```

---

## 非交互式模式

对于自动化场景，提供非交互式脚本：

```bash
bash skills/qgw-init/scripts/qgw-init.sh \
  --platform claude \
  --mode full \
  --yes
```

完整参数说明 → 见 [scripts/qgw-init.sh](scripts/qgw-init.sh) 头部注释。

---

## 目录结构

```
qgw-init/
├── SKILL.md                            ← 主入口（本文件）
├── scripts/
│   └── qgw-init.sh                     ← 非交互式快速初始化脚本
├── references/
│   ├── platform-configs.md             ← 各平台适配器配置详情
│   └── workflow-modes.md               ← 三种工作流模式差异说明
└── CHANGELOG.md
```

## 参考

- [平台适配器配置](references/platform-configs.md)
- [工作流模式说明](references/workflow-modes.md)
- [quality-gate-workflow 安装指南](../quality-gate-workflow/references/installation.md)
- [项目配置](../quality-gate-workflow/references/project-config.md)
