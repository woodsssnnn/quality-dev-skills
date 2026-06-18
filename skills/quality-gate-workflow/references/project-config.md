# 项目配置

## Extensions/Presets：`.qgw/` 覆盖目录

在项目根目录创建 `.qgw/` 目录进行定制，无需修改 skill 文件：

```
.qgw/
├── config.json              # 项目 QGW 配置
├── constitution.md          # 项目 constitution
├── anti-patterns.md         # 项目专属 anti-patterns（追加到全局）
├── templates/
│   ├── advisor-pm.md        # 覆盖 PM 顾问 prompt
│   ├── advisor-arch.md      # 覆盖架构师顾问 prompt
│   ├── verifier-gate1.md    # 覆盖 Gate 1 verifier prompt
│   ├── verifier-gate2.md    # 覆盖 Gate 2 verifier prompt
│   └── report-template.md   # 覆盖报告模板
└── overrides/
    └── gate1-steps.md       # 覆盖/追加 Gate 1 步骤
```

### 优先级解析

```
1. .qgw/ 项目本地覆盖（最高优先级）
2. skill 默认 references/
```

当 `.qgw/templates/advisor-pm.md` 存在时，替代 `references/advisor-templates.md` 中的 PM 顾问部分。

### config.json

```json
{
  "preset": "enterprise",
  "language": "zh",
  "hooks": { "mode": "strict" },
  "overrides": {
    "advisor_pm": ".qgw/templates/advisor-pm.md",
    "verifier_gate2": ".qgw/templates/verifier-gate2.md"
  }
}
```

## Preset 预设包

Preset 是参数组合的场景化别名，**不绕过任何门禁**，展开后仍走完整 Gate 流程。

### 内置预设

| Preset | 等价参数 | 场景 | 说明 |
|--------|----------|------|------|
| `quickfix` | `--gate2 --debug` | 快速修 Bug | 无 Plan，直接定位并修复 |
| `feature` | `--all --strict` | 完整功能开发 | 全流程 + 零偏差 |
| `hotfix` | `--gate1 --bug` + `--gate2 --debug` | 紧急 Bug 修复 | 先分析 Bug 再生成修复 Plan 并实现 |
| `review` | `--self` | 复盘最近会话 | 检查步骤完整性和执行质量 |
| `audit` | `--gate2 --audit` | 审计已有代码 | 只检查不修改 |
| `minimal` | `--gate1 --lite` + `--gate2 --incremental` | 轻量快速通道 | 适合小改动 |

### 使用方式

```bash
# 方式 1：命令行参数
--preset quickfix

# 方式 2：.qgw/config.json 中设置默认 preset
{ "preset": "quickfix" }

# 方式 3：智能推断时自动建议（零参数模式）
```

### 自定义 Preset

在 `.qgw/config.json` 中定义项目专属 preset：

```json
{
  "presets": {
    "my-workflow": {
      "gate1": "--prd",
      "gate2": "--impl --e2e"
    }
  }
}
```

> 自定义 preset 同样不绕过门禁，只是简化参数记忆。

## CLAUDE.md 配置

| 配置项 | 位置 | 说明 |
|--------|------|------|
| `dev_rule_path` | 项目 CLAUDE.md | 项目开发规范技能路径（推荐） |
| `gate_dev_rules` | 项目 CLAUDE.md（兼容旧方式） | Gate 1 模式选择 + Gate 2 编码规范 |
| `gate_search_paths` | 项目 CLAUDE.md（可选） | P1.6 代码链路调查的搜索目录列表 |
| `gate1_constitution` | 项目 CLAUDE.md（可选）或 `.qgw/constitution.md` | 需求解析约束 |

### dev_rule_path 配置（推荐）

项目CLAUDE.md中声明开发规范技能路径：

```markdown
## 项目开发规范

- 技能位置：`.agents/skills/project-dev-rule/`
- 使用project-dev-rule作为开发规范
```

quality-gate-workflow运行时会：
1. 检查 `dev_rule_path` 配置
2. 如果存在，加载对应的技能
3. 如果不存在，使用通用规范（fallback）

### gate_dev_rules 配置（兼容旧方式）

旧项目仍可使用 `gate_dev_rules` 配置，但推荐迁移到 `dev_rule_path`。

```markdown
## Gate 配置

- gate_dev_rules: your-project-dev-rule
```
