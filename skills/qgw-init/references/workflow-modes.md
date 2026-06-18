# 工作流模式说明

QGW 提供三种工作流模式，根据项目复杂度和变更规模选择合适的模式。

---

## 模式总览

| 模式 | 参数 | 核心理念 | 适用场景 |
|------|------|----------|----------|
| **lite** | `--lite` | 轻量快速 | 单文件改动、快速修 Bug、小重构 |
| **full** | （默认） | 完整流程 | 标准功能开发、多文件变更 |
| **ultra** | `--strict --e2e` | 零容忍 | 关键系统、金融/医疗、端到端验证 |

---

## lite 模式（轻量）

### 适用场景

- 单文件修改（配置调整、文案修改、样式调整）
- 快速修 Bug（已知问题根因）
- 小型重构（不改变接口）
- 文档更新

### 触发方式

```bash
# 初始化时选择 lite
bash qgw-init.sh --mode lite

# 运行时触发
--gate1 --lite
--gate2 --lite
```

### 执行的步骤

```
Gate 1 (lite):
  P0: 环境检查         ✅ 执行
  P1: 需求分析         ✅ 执行（精简版）
  P1.5: 顾问咨询       ❌ 跳过
  P2: Plan 生成        ✅ 执行
  P3: 验收清单         ✅ 执行（简化）
  P4: Verifier 验证    ❌ 跳过

Gate 2 (lite):
  S0: 环境检查         ✅ 执行
  S1: Plan 解析        ✅ 执行
  S2: 代码实现         ✅ 执行
  S3: 自测             ✅ 执行（仅单元测试）
  S3.5: DB 验证        ❌ 跳过
  S4: Verifier 验证    ❌ 跳过
  S5: 回归测试         ❌ 跳过
  S6: 报告生成         ❌ 跳过
```

### 跳过的步骤

| 步骤 | 原因 |
|------|------|
| 顾问咨询（P1.5） | 单文件改动不需要多角色评审 |
| Verifier 验证（P4/S4） | 简化流程，信任开发者判断 |
| DB 验证（S3.5） | 小改动通常不涉及数据库变更 |
| 回归测试（S5） | 影响范围有限 |
| 报告生成（S6） | 无需审计记录 |

### config.json 配置

```json
{
  "mode": "lite",
  "engine": {
    "enabled": true,
    "strict_mode": false
  }
}
```

---

## full 模式（完整）

### 适用场景

- 标准功能开发（新增功能、新模块）
- 多文件变更（跨模块修改）
- 需要验证的需求（接口变更、数据模型变更）
- 团队协作功能（需要审计记录）

### 触发方式

```bash
# 初始化时选择 full（默认）
bash qgw-init.sh --mode full

# 运行时触发（默认模式，无需额外参数）
--gate1
--gate2
--all
```

### 执行的步骤

```
Gate 1 (full):
  P0: 环境检查         ✅ 执行
  P1: 需求分析         ✅ 执行
  P1.5: 顾问咨询       ✅ 执行
  P2: Plan 生成        ✅ 执行
  P3: 验收清单         ✅ 执行
  P4: Verifier 验证    ✅ 执行

Gate 2 (full):
  S0: 环境检查         ✅ 执行
  S1: Plan 解析        ✅ 执行
  S2: 代码实现         ✅ 执行
  S3: 自测             ✅ 执行
  S3.5: DB 验证        ✅ 执行（如有 DB MCP）
  S4: Verifier 验证    ✅ 执行
  S5: 回归测试         ✅ 执行
  S6: 报告生成         ✅ 执行
```

### 所有步骤完整执行，无跳过。

### config.json 配置

```json
{
  "mode": "full",
  "engine": {
    "enabled": true,
    "strict_mode": true
  }
}
```

---

## ultra 模式（超严格）

### 适用场景

- 关键系统（金融交易、医疗系统、安全模块）
- 零容忍场景（不允许任何偏差）
- 合规要求（需要通过审计的变更）
- 大规模重构（核心架构变更）

### 触发方式

```bash
# 初始化时选择 ultra
bash qgw-init.sh --mode ultra

# 运行时触发
--gate1 --strict --e2e
--gate2 --strict --e2e
--all --strict --e2e
```

### 执行的步骤

```
Gate 1 (ultra):
  P0: 环境检查         ✅ 执行（增强检查）
  P1: 需求分析         ✅ 执行（深度分析）
  P1.5: 顾问咨询       ✅ 执行（所有顾问角色）
  P2: Plan 生成        ✅ 执行（含风险评估）
  P3: 验收清单         ✅ 执行（详细版）
  P4: Verifier 验证    ✅ 执行（零偏差容忍）
  P5: 交叉审查         ✅ 执行（ultra 独有）

Gate 2 (ultra):
  S0: 环境检查         ✅ 执行（增强检查）
  S1: Plan 解析        ✅ 执行（逐行验证）
  S2: 代码实现         ✅ 执行（增量 checkpoint）
  S3: 自测             ✅ 执行（单元+集成+E2E）
  S3.5: DB 验证        ✅ 执行（强制要求）
  S4: Verifier 验证    ✅ 执行（零偏差容忍）
  S5: 回归测试         ✅ 执行（完整回归套件）
  S6: 报告生成         ✅ 执行（含审计报告）
  S7: 交叉验证         ✅ 执行（ultra 独有）
```

### ultra 独有步骤

| 步骤 | 说明 |
|------|------|
| P5: 交叉审查 | 使用第二个 Verifier 独立验证 Gate 1 产出，两者一致才通过 |
| S7: 交叉验证 | 使用第二个 Verifier 独立验证代码实现，两者一致才通过 |

### ultra 额外约束

| 约束 | 说明 |
|------|------|
| 零偏差容忍 | Verifier 发现任何偏差即 BLOCK，不允许 WARN 降级 |
| 强制 DB MCP | 如无数据库 MCP 配置，直接 BLOCK（不允许降级为静态分析） |
| 增量 checkpoint | 每实现一个验收项即写入 checkpoint，不允许批量提交 |
| E2E 测试强制 | 必须包含端到端测试用例，否则 Verifier 不通过 |
| 双重验证 | 两个独立 Verifier 必须一致通过 |

### config.json 配置

```json
{
  "mode": "ultra",
  "engine": {
    "enabled": true,
    "strict_mode": true
  }
}
```

---

## 模式切换

### 初始化后切换模式

修改 `.qgw/config.json` 中的 `mode` 字段：

```json
{
  "mode": "lite"
}
```

或在运行时通过参数覆盖：

```bash
# 项目默认 full，本次用 lite
--gate2 --lite

# 项目默认 lite，本次用 ultra
--all --strict --e2e
```

### 运行时参数覆盖优先级

```
运行时参数 > .qgw/config.json > 默认值
```

---

## 参数组合速查

| 场景 | 推荐模式 | 参数组合 |
|------|----------|----------|
| 修改一行配置 | lite | `--gate2 --lite` |
| 修复已知 Bug | lite | `--gate2 --debug --lite` |
| 新增 API 接口 | full | `--all` |
| 数据库 Schema 变更 | full | `--gate1` + `--gate2` |
| 金融模块改动 | ultra | `--all --strict --e2e` |
| 核心架构重构 | ultra | `--gate1 --strict` + `--gate2 --strict --e2e` |
| 文档更新 | lite | `--gate1 --lite`（仅生成 Plan） |

---

## 模式与 Preset 的关系

Preset 是参数组合的别名，可以在任何模式下使用：

```bash
# quickfix preset + lite 模式
--preset quickfix --lite    # = --gate2 --debug --lite

# feature preset + ultra 模式
--preset feature --strict --e2e    # = --all --strict --e2e
```

Preset 不绕过任何门禁，只是在当前模式基础上叠加参数。
