# 技能间通信协议 (Skill Protocol)

定义 quality-dev-skills 各技能之间的数据交换、状态传递和事件通知规范。

## 1. Artifact 协议

技能通过 `docs/` 目录下的约定路径交换数据产物。

### 路径约定

| 路径模式 | 生产者 | 消费者 | 说明 |
|---------|--------|--------|------|
| `docs/plans/*.md` | quality-gate-workflow (Gate 1) | quality-gate-workflow (Gate 2), verifier | Plan 文件 |
| `docs/reports/*.md` | quality-gate-workflow (Gate 2) | skill-optimizer | 执行报告 |
| `docs/verification/*.md` | quality-gate-workflow (Verifier) | quality-gate-workflow (Gate 2) | 验证结果 |
| `docs/INDEX.md` | 所有技能 | 所有技能 | Master Index，注册产物路径 |

### 规则

- **写入前注册**：任何技能写入 artifact 前，必须先在 `docs/INDEX.md` 注册路径
- **只追加不覆盖**：artifact 文件一旦创建，其他技能不得覆盖，只能追加或创建新版本
- **命名规范**：文件名包含时间戳或版本号，如 `plan-2026-06-18-v1.md`

## 2. 状态协议

通过 `.qgw-engine-state.json` 传递执行状态。

### 状态文件结构

```json
{
  "engine_version": "0.8.0.0",
  "session_id": "uuid",
  "status": "RUNNING | COMPLETED | BLOCKED | FAILED",
  "current_phase": "gate1 | gate2 | verify | audit",
  "current_step": "P1 | P2 | ... | S4",
  "started_at": "ISO 8601",
  "updated_at": "ISO 8601",
  "steps_completed": ["P1", "P2"],
  "skip_matrix": {},
  "artifacts_produced": ["docs/plans/plan-v1.md"],
  "errors": []
}
```

### 规则

- **单写者**：只有 gate-enforcer.py 可以写入状态文件
- **多读者**：所有技能可读取状态文件判断当前阶段
- **原子更新**：每次状态变更必须完整写入，不得部分更新

## 3. 事件协议

技能间通过约定文件实现异步通知。

### 事件类型

| 事件 | 文件路径 | 触发者 | 监听者 |
|------|---------|--------|--------|
| `gate1_complete` | `.qgw/events/gate1-done.flag` | quality-gate-workflow | skill-optimizer, 垂直技能 |
| `gate2_complete` | `.qgw/events/gate2-done.flag` | quality-gate-workflow | 所有下游技能 |
| `plan_changed` | `.qgw/events/plan-changed.flag` | quality-gate-workflow | verifier, 垂直技能 |
| `optimization_done` | `.qgw/events/opt-done.flag` | skill-optimizer | quality-gate-workflow |

### 事件文件格式

```
TIMESTAMP=2026-06-18T10:30:00Z
SOURCE=quality-gate-workflow
EVENT=gate1_complete
ARTIFACT=docs/plans/plan-v1.md
```

### 规则

- **幂等处理**：监听者必须能处理重复事件
- **过期清理**：新 session 开始时清空 `.qgw/events/` 目录

## 4. 接口声明

每个技能在 `skill-manifest.json` 中声明 inputs/outputs，供其他技能查询。

### 声明规范

```json
{
  "inputs": {
    "required": ["PRD 文件或需求描述"],
    "optional": ["--strict", "--lite"]
  },
  "outputs": {
    "artifacts": ["docs/plans/*.md"],
    "side_effects": ["更新 INDEX.md"]
  }
}
```

### 依赖检查

gate-enforcer.py 在初始化时检查：
1. 所需 artifact 的生产者技能是否存在于 manifest
2. 声明的 tools 在当前平台是否可用
3. 依赖的 skills 版本是否满足 `min_version` 约束

## 5. 版本兼容

- 技能间通信格式变更必须更新 `generator_version`
- manifest schema 变更遵循 SemVer：Minor 版本新增字段，Major 版本破坏兼容
- 所有技能必须声明 `compatibility.min_version`

## 6. 技能命名规范

基于 `shared/agent-skills-best-practices.md` §3.1 的动名词推荐，确立本项目命名标准。

### 6.1 命名格式

- **统一格式**：kebab-case（小写字母 + 连字符）
- **禁止**：下划线、大写字母、空格、连续连字符

### 6.2 命名分类

| 分类 | 命名模式 | 示例 | 说明 |
|------|---------|------|------|
| **仓库内技能** | 描述能力（不是实现） | `quality-gate-workflow`、`skill-optimizer` | 放在 `skills/` 目录 |
| **垂直技能** | 领域+能力 | `api-design-review`、`db-migration-gate` | 放在 `skills/` 目录 |
| **项目级技能** | 固定名 `project-dev-rule` | `project-dev-rule` | 模板生成物，不随项目变 |
| **共享模板** | `*-template` 后缀 | `project-dev-rule-template`、`skill-template` | 放在 `shared/` 目录 |

### 6.3 当前技能清单

| ID | 类别 | 命名评估 |
|----|------|----------|
| `quality-gate-workflow` | 核心引擎 | ✅ 保持，已广泛使用 |
| `skill-optimizer` | 优化框架 | ✅ 保持，描述清晰 |
| `qgw-init` | 初始化 | ✅ 保持，QGW 生态内约定俗成 |
| `api-design-review` | 垂直技能 | ✅ 保持，动名词形式 |
| `db-migration-gate` | 垂直技能 | ✅ 保持，名词短语可接受 |
| `project-dev-rule` | 项目级 | ✅ 保持，固定名不随项目变 |

### 6.4 避免的命名

- 模糊名称：`helper`、`utils`、`tools`
- 过于泛化：`documents`、`data`、`files`
- 缩写不展开：除非已约定俗成（如 `qgw`）
- 集合内命名不一致：同一类技能应遵循相同模式
