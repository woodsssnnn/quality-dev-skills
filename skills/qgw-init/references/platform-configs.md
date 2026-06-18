# 平台适配器配置详情

QGW 支持 5 个 AI 平台，每个平台的配置方式和文件位置不同。本文档给出每个平台的完整配置示例。

---

## 1. Claude Code

**配置文件**: `.claude/settings.local.json`

### 自动检测条件

项目根目录存在 `.claude/` 目录。

### 完整配置示例

```json
{
  "env": {
    "QGW_HOOK_MODE": "strict",
    "QGW_PLATFORM": "claude",
    "QGW_ENGINE_ENABLED": "true"
  },
  "permissions": {
    "allow": [
      "Bash(bash */quality-gate-workflow/scripts/*)",
      "Bash(python */quality-gate-workflow/scripts/*)",
      "Bash(bash */qgw-init/scripts/*)"
    ]
  }
}
```

### 配置项说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `env.QGW_HOOK_MODE` | Hook 检查模式：`strict`（阻止提交）/ `warn`（仅警告）/ `off`（关闭） | `strict` |
| `env.QGW_PLATFORM` | 平台标识 | `claude` |
| `env.QGW_ENGINE_ENABLED` | 是否启用确定性执行引擎 | `true` |
| `permissions.allow` | 允许执行的脚本权限 | — |

### Hook 支持

Claude Code 原生支持 `preToolUse` Hook，可在 `.claude/settings.local.json` 中配置 git commit 前自动运行 `verify-checkpoint.sh`。

---

## 2. Codex

**配置文件**: `AGENTS.md`（项目根目录）

### 自动检测条件

项目根目录存在 `AGENTS.md` 且文件内含 "codex" 关键词。

### 完整配置示例

```markdown
# Project Agents Configuration

## QGW 质量门禁

- 平台: codex
- 模式: full
- 触发: `--gate1` / `--gate2` / `--all` / `--self`
- 配置: `.qgw/config.json`
- 文档目录: `docs/plans/` `docs/verification/` `docs/reports/` `docs/sessions/`

## 快速开始

```bash
# Gate 1: 需求 → Plan
--gate1

# Gate 2: Plan → 代码
--gate2

# 全流程
--all
```

## 开发规范

- 使用 `.qgw/constitution.md` 中的需求约束
- 所有产出物写入 `docs/` 子目录
- 遵循 Gate 1 → Gate 2 的顺序执行
```

### 特殊说明

- Codex 不支持 Hook 机制，`verify-checkpoint.sh` 需手动运行
- `AGENTS.md` 同时作为项目级 Agent 指令文件，QGW 配置追加在末尾
- 如已有 `AGENTS.md`，qgw-init 只追加 QGW 段落，不覆盖其他内容

---

## 3. OpenCode

**配置文件**: `plugin.mjs`（ES Module 插件）

### 自动检测条件

项目根目录存在 `opencode.config.*` 文件。

### 完整插件配置（opencode.config.qgw.json）

```json
{
  "plugins": {
    "quality-dev-skills": {
      "platform": "opencode",
      "mode": "full",
      "hooks": { "mode": "strict" },
      "paths": {
        "config": ".qgw/config.json",
        "constitution": ".qgw/constitution.md"
      }
    }
  }
}
```

### 插件机制（plugin.mjs）

OpenCode 通过 `experimental.chat.system.transform` 钩子在每轮对话注入 QGW 指令：

```javascript
export default async ({ client } = {}) => {
  return {
    'experimental.chat.system.transform': async (_input, output) => {
      const mode = readMode(); // 从状态文件读取当前模式
      if (mode === 'off') return;
      output.system.push(getQualityGateInstructions(mode));
    },
    'command.execute.before': async (input) => {
      // 持久化 /quality-dev-skills <level> 命令
      if (!input || input.command !== 'quality-dev-skills') return;
      const mode = (input.arguments || '').trim() || 'full';
      writeMode(mode);
    },
  };
};
```

### 模式切换

在 OpenCode 中通过命令切换 QGW 注入模式：

```
/quality-dev-skills full    # 完整模式
/quality-dev-skills lite    # 轻量模式
/quality-dev-skills off     # 关闭注入
```

---

## 4. MiMoCode

**配置文件**: `.mimo/qgw-plugin.json`

### 自动检测条件

项目根目录存在 `.mimo/` 目录。

### 完整配置示例

```json
{
  "name": "quality-dev-skills",
  "platform": "mimo",
  "mode": "full",
  "hooks": { "mode": "strict" },
  "config": ".qgw/config.json",
  "constitution": ".qgw/constitution.md"
}
```

### 配置项说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `name` | 插件名称 | `quality-dev-skills` |
| `platform` | 平台标识 | `mimo` |
| `mode` | 工作流模式：`lite` / `full` / `ultra` | `full` |
| `hooks.mode` | Hook 模式：`strict` / `warn` / `off` | `strict` |
| `config` | QGW 配置文件路径 | `.qgw/config.json` |
| `constitution` | 项目 constitution 路径 | `.qgw/constitution.md` |

### 特殊说明

- MiMoCode 的插件系统通过 `.mimo/` 目录管理
- `plugin.json` 中 `skills` 字段指向技能目录
- 支持 Lifecycle hooks 能力

---

## 5. General（通用平台）

**配置文件**: `AGENTS.md`（项目根目录）

### 自动检测条件

以上 4 个平台均未匹配时的 fallback。

### 完整配置示例

```markdown
# Project Agents Configuration

## QGW 质量门禁

- 平台: general
- 模式: full
- 触发: `--gate1` / `--gate2` / `--all` / `--self`
- 配置: `.qgw/config.json`
- 文档目录: `docs/plans/` `docs/verification/` `docs/reports/` `docs/sessions/`

## 快速开始

```bash
# Gate 1: 需求 → Plan
--gate1

# Gate 2: Plan → 代码
--gate2

# 全流程
--all

# 自检
--self
```

## 安装技能

```bash
git clone https://gitcode.com/songnan/quality-dev-skills.git ~/quality-dev-skills
cd ~/quality-dev-skills
bash scripts/install.sh
```

## 更多信息

- [README](../../README.md)
- [安装指南](../../INSTALL.md)
```

### 特殊说明

- General 平台与 Codex 使用相同的 `AGENTS.md` 文件，但 platform 标识不同
- General 不假设任何平台特有能力（Hook、插件系统等）
- 所有 QGW 功能通过 prompt 触发，不依赖平台集成

---

## 平台能力对比

| 能力 | Claude Code | Codex | OpenCode | MiMoCode | General |
|------|:-----------:|:-----:|:--------:|:--------:|:-------:|
| Hook（pre-commit） | ✅ | ❌ | ❌ | ⚠️ 部分 | ❌ |
| 自动指令注入 | ✅ | ❌ | ✅ | ✅ | ❌ |
| Lifecycle hooks | ✅ | ✅ | ✅ | ✅ | ❌ |
| 环境变量配置 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 模式热切换 | ✅ | ❌ | ✅ | ❌ | ❌ |
| `AGENTS.md` 支持 | ❌ | ✅ | ❌ | ❌ | ✅ |

---

## 切换平台

如需切换平台，重新运行初始化即可：

```bash
# 交互式
--init

# 非交互式
bash skills/qgw-init/scripts/qgw-init.sh --platform opencode --force --yes
```

使用 `--force` 覆盖已有平台配置。
