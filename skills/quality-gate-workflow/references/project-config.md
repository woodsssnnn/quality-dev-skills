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
  },
  "engine": {
    "enabled": true,
    "strict_mode": true,
    "state_file": "docs/.qgw-engine-state.json",
    "checkpoint_dir": "docs/.qgw-checkpoints"
  }
}
```

### engine 配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | bool | `true` | 是否启用确定性执行引擎。设为 `false` 则跳过所有 gate-enforcer 调用（纯 prompt 模式） |
| `strict_mode` | bool | `true` | 严格模式下，引擎 BLOCK 时禁止继续。关闭后仅警告 |
| `state_file` | string | `docs/.qgw-engine-state.json` | 引擎状态文件路径 |
| `checkpoint_dir` | string | `docs/.qgw-checkpoints` | 步骤 checkpoint 文件目录 |

> 引擎配置也可通过环境变量覆盖：`QGW_ENGINE_ENABLED=false`、`QGW_ENGINE_STATE=custom/path.json`

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

## reference_skills：参考技能声明

声明上游技能作为参考资源（不是依赖）。Gate 2 S2 实现时按需加载。

```json
{
  "reference_skills": [
    {
      "id": "-dev-rule",
      "path": ".claude/skills/-dev-rule",
      "role": "pattern_source",
      "load_scope": ["references/backend/patterns", "references/frontend/patterns", "references/frontend/rules"]
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 技能标识符 |
| `path` | string | 技能目录路径（相对项目根目录） |
| `role` | string | 角色类型：`pattern_source`（模式参考） / `rule_source`（规则参考） |
| `load_scope` | string[] | 加载范围（仅加载指定子目录，避免全量加载） |

**与 project-dev-rule 的关系**：参考技能是只读输入，project-dev-rule 是活输出。冲突时 project-dev-rule 优先。

## advisor：顾问角色配置

配置顾问子代理的项目身份注入参数。

```json
{
  "advisor": {
    "project_domain": "TCL Finance — 基于  5.2.0 流程管理平台的客户定制交付项目",
    "tech_stack": "后端 Java/Spring Boot/MyBatis, 前端 React/Next.js/antd v4/Formily",
    "glossary_path": ".qgw/glossary.md",
    "conventions_summary_path": ".agents/skills/project-dev-rule/SKILL.md"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `project_domain` | string | 项目业务领域描述，注入 PM/架构师顾问 prompt |
| `tech_stack` | string | 技术栈摘要，注入顾问 prompt |
| `glossary_path` | string | 术语表文件路径，注入 PM 顾问 prompt |
| `conventions_summary_path` | string | 编码规范摘要路径，注入架构师顾问 prompt |

变量解析规则详见 `advisor-templates.md` “变量注入机制”章节。

## dev_rule：自进化配置

配置 project-dev-rule 的自进化行为。

```json
{
  "dev_rule": {
    "path": ".agents/skills/project-dev-rule",
    "auto_evolve": true,
    "evolve_threshold": {
      "error_pattern_frequency": 3,
      "advisor_cluster_size": 3
    }
  }
}
```

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `path` | string | `.agents/skills/project-dev-rule` | dev-rule 技能目录路径 |
| `auto_evolve` | bool | `true` | 是否在 Gate 完成后自动执行 evolve 检查 |
| `evolve_threshold.error_pattern_frequency` | int | `3` | error-patterns 升级为核心规则的频率阈值 |
| `evolve_threshold.advisor_cluster_size` | int | `3` | 顾问根因簇升级为核心规则的数量阈值 |

### 向后兼容

| 旧配置 | 新配置 | 迁移方式 |
|---------|---------|----------|
| CLAUDE.md `dev_rule_path` | `dev_rule.path` | 两者均支持，新配置优先 |
| CLAUDE.md `gate_dev_rules` | `reference_skills` | `gate_dev_rules` 作为 reference_skills 的简化别名 |
| 无 | `advisor` | 纯新增字段，不影响旧项目 |
