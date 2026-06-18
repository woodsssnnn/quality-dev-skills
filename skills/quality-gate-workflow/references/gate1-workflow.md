# Gate 1 工作流详细步骤

## 日志格式规范

**统一格式**：所有步骤必须使用以下结构化日志格式：

```
[qgw][{timestamp}][{platform}:{session_id}][{gate}][{step}/{total}] {status} {message}
```

| 字段 | 说明 | 示例 |
|------|------|------|
| `[qgw]` | 固定前缀 | `[qgw]` |
| `{timestamp}` | ISO时间戳 | `2026-06-17T20:45:00` |
| `{platform}` | 平台标识 | `mimo` / `claude` / `codex` / `opencode` |
| `{session_id}` | 完整会话ID | `ses_12ca2c1c4ffe0S3HguaG7fosHN` |
| `{gate}` | 阶段 | `gate1` / `gate2` / `analyze` |
| `{step}/{total}` | 步骤进度 | `P1/5` / `S3/5` |
| `{status}` | 状态图标 | ✅ / ❌ / ⚠️ / 🔄 / → |
| `{message}` | 消息内容 | `解析需求完成: 99项可验证项` |

**平台标识**：

| 平台 | 标识 | 会话存储位置 | 类型 |
|------|------|--------------|------|
| MiMoCode | `mimo` | `~/.local/share/mimocode/memory/sessions/` | 国内 |
| 通义灵码 | `tongyi` | `~/.local/share/tongyi/sessions/` | 国内 |
| 豆包MarsCode | `marscode` | `~/.local/share/marscode/sessions/` | 国内 |
| 百度Comate | `comate` | `~/.local/share/comate/sessions/` | 国内 |
| CodeGeeX | `codegeex` | `~/.local/share/codegeex/sessions/` | 国内 |
| Cursor | `cursor` | `~/.cursor/sessions/` | 国际 |
| Claude Code | `claude` | `~/.claude/projects/{project-slug}/` | 国际 |
| Codex | `codex` | `~/.codex/sessions/{year}/` | 国际 |
| OpenCode | `opencode` | `~/.opencode/sessions/` | 国际 |

**状态图标**：
- ✅ 步骤完成
- ❌ 步骤失败
- ⚠️ 警告/发现ISSUE
- 🔄 步骤进行中
- → 步骤开始/转移

**示例**：
```bash
[qgw][2026-06-17T20:45:00][mimo:ses_12ca2c1c4ffe0S3HguaG7fosHN][gate1][P0/5] → 工作空间检查
[qgw][2026-06-17T20:45:05][mimo:ses_12ca2c1c4ffe0S3HguaG7fosHN][gate1][P1/5] ✅ 解析需求完成: 99项可验证项, 5个unit
[qgw][2026-06-17T20:45:30][mimo:ses_12ca2c1c4ffe0S3HguaG7fosHN][gate1][STATS] 📊 总耗时: 30s | 步骤: 5/5 | 通过率: 100%
```

**复盘路径**：
```bash
# MiMoCode会话
cat ~/.local/share/mimocode/memory/sessions/{session_id}/checkpoint.md

# Claude Code会话
cat ~/.claude/projects/{project-slug}/conversations/{session-id}.json

# Codex会话
cat ~/.codex/sessions/2026/{session-id}/history.json

# 国内平台
cat ~/.local/share/tongyi/sessions/{session_id}/checkpoint.md    # 通义灵码
cat ~/.local/share/marscode/sessions/{session_id}/checkpoint.md  # 豆包MarsCode
cat ~/.local/share/comate/sessions/{session_id}/checkpoint.md    # 百度Comate
```

## 5问题重启测试

借鉴 planning-with-files，会话恢复时必须通过5问题测试：

| 问题 | 答案来源 | 验证方式 |
|------|----------|----------|
| **我在哪？** | 当前阶段 | `docs/QGW-INDEX.md` Active Sessions |
| **我要去哪？** | 剩余阶段 | Plan文档的Phase列表 |
| **目标是什么？** | 需求目标 | Plan文档的Goal声明 |
| **学到了什么？** | 发现和决策 | `docs/verification/*.json` |
| **做了什么？** | 执行记录 | `docs/sessions/*.md` |

**执行时机**：
- 会话启动时（on-session-start hook）
- /clear 恢复后
- context compaction 后
- 长时间暂停后恢复

**验证失败处理**：
- 无法回答任一问题 → 输出 `[qgw] ⚠️ 会话状态不完整，需要重新加载`
- 自动尝试从文件恢复
- 恢复失败 → 提示用户手动恢复

## 2-Action Rule

借鉴 planning-with-files，每2次view/search操作后必须更新文件：

```markdown
操作1: Grep搜索 → 记录发现
操作2: Read文件 → 必须更新 findings
操作3: Glob搜索 → 记录发现
操作4: Grep搜索 → 必须更新 findings
```

**适用场景**：
- P1.5 数据库调查
- P1.6 代码链路调查
- Gate 2 代码实现

**执行方式**：
- 每2次操作后自动提醒
- 更新对应的verification JSON或session summary
- 防止信息丢失

## 3-Strike Error Protocol

借鉴 planning-with-files，错误处理必须遵循3次尝试协议：

```markdown
尝试1: 诊断并修复
  → 仔细阅读错误信息
  → 识别根因
  → 应用针对性修复

尝试2: 替代方法
  → 相同错误？尝试不同方法
  → 不同工具？不同库？
  → 绝不重复完全相同的操作

尝试3: 重新思考
  → 质疑假设
  → 搜索解决方案
  → 考虑更新计划

3次失败后: 升级给用户
  → 解释尝试了什么
  → 分享具体错误
  → 请求指导
```

**执行规则**：
- 错误必须记录到Plan文档的Errors Encountered表
- 每次尝试必须记录到progress.md
- 3次失败后必须停止并报告用户
- 禁止静默跳过错误

---

## P0：工作空间初始化

> 输出: `[qgw][{timestamp}][{session_id}][gate1][P0/5] → 工作空间检查 ...`
> 完成: `[qgw][{timestamp}][{session_id}][gate1][P0/5] ✅ 目录就绪` 或 `✅ 已创建`

**引擎交互**（必须）：
- 开始前: `python gate-enforcer.py enter P0` → 必须收到 `ALLOW`
- 完成后: `python gate-enforcer.py complete P0` → 引擎验证目录已创建

检查并创建工作空间目录（如果不存在）：

```bash
mkdir -p docs/plans docs/verification docs/reports docs/sessions
```

检查结果：
- `docs/plans/` 存在 → ✅
- `docs/plans/` 不存在 → 创建并输出 `[qgw:gate1:P0] ✅ 已创建 docs/plans/`
- 同理处理 `docs/verification/`、`docs/reports/`、`docs/sessions/`

### Master Index 初始化

检查 `docs/QGW-INDEX.md` 是否存在：
- 不存在 → 创建初始 INDEX（格式见 SKILL.md "Master Index" 章节），注册当前 session 行（status=IN_PROGRESS）
- 已存在 → 追加当前 session 行

### Session 注册

在 `docs/QGW-INDEX.md` 的 Active Sessions 表追加：

```
| {session-id} | {date} | gate1 | IN_PROGRESS | {plan-file} | — | — |
```

### PRD diff 检测（增量 Gate 1）

当存在已有 Plan（`docs/plans/` 非空）时，P0 额外检查：
1. 读取已有 Plan 的 `source` 字段 → 获取 PRD 路径
2. 对比 PRD 文件修改时间 vs Plan 生成时间
3. 如 PRD 有修改 → 输出 `[qgw:gate1:P0] ⚠️ PRD 文件自上次 Gate 1 后有修改`
4. 列出受影响的章节 → 标记对应可验证项为 NEEDS_REVIEW
5. 询问用户：增量更新（仅处理变更部分）或全量重跑

**禁止**：因目录不存在而跳过后续步骤或静默跳过 JSON 写入。目录缺失必须先创建再继续。

---

## --lite 轻量快速通道

当用户指定 `--lite` 参数时，Gate 1 流程简化为 P1→P2→P4→P5，跳过 P1.5/P1.6/P1.7。

### 适用条件（必须全部满足）

- 单文件/单函数改动（不涉及跨文件依赖）
- 纯前端且无 DB 变更，或 bug fix 改动 ≤3 处
- 无架构决策（单 unit、无共享组件修改）

### 跳过步骤

| 步骤 | 跳过原因 |
|------|---------|
| P1.5 DB 调查 | 改动不涉及 SQL/Mapper/Service |
| P1.6 代码链路调查 | 单文件改动，无需跨层 grep |
| P1.7 PM 顾问 | 改动明确，无业务歧义风险 |

### 保留步骤

| 步骤 | 说明 |
|------|------|
| P1 | 仍需提取可验证项（具体、可追溯 §X.X） |
| P2 | 仍需撰写 plan（What/Where/How） |
| P4 | 仍需独立 verifier 验证 plan ↔ PRD 一致性 |
| P5 | 仍需持久化验收清单 |

### 日志输出

```
[qgw:gate1:P1-check] --lite 模式: P1.5=跳过(lite) | P1.6=跳过(lite) | P1.7=跳过(lite)
```

---

## P1：解析需求 → 提取可验证项

> 输出: `[qgw][{timestamp}][{session_id}][gate1][P1/5] → 解析需求 → 提取可验证项 ...`
> 完成: `[qgw][{timestamp}][{session_id}][gate1][P1/5] ✅ 解析需求完成: N项可验证项, M个unit`

**引擎交互**（必须）：
- 开始前: `python gate-enforcer.py enter P1` → 必须收到 `ALLOW`
- 完成后: `python gate-enforcer.py complete P1 --meta '{"has_backend": true|false, "is_greenfield": true|false}'` → 引擎根据 meta 自动处理 P1.5 skip

重读需求文档，提取每个可验证的字段级规格。每项必须具体、可追溯、可测试。**每个可验证项必须追溯到 PRD 具体 §X.X 章节**，禁止无引用的断言。

| 类别 | 好的项 | 差的（太模糊） |
|------|--------|--------------|
| 组件类型 | "筛选器=流程树多选 (§6.1.1)" | "有筛选功能" |
| 字段存在 | "跟进人页面无审核人字段 (§6.3.3)" | "字段正确" |
| 必填/默认 | "计划完成时间必填受配置控制 (§6.3.1)" | "时间可填" |
| 显示顺序 | "调查→活动检查→问题→跟进 (§6.3.4)" | "按PRD排列" |
| 数据来源 | "责任部门=dutyDeptName (§6.1)" | "显示部门" |
| 条件逻辑 | "说明始终显示(必填)+附件始终显示(非必填) (§6.3.4)" | "有说明和附件" |

格式（同时写入结构化 JSON，schema 见 `acceptance-criteria-schema.json`）：

```
## Verifiable Items: [需求名称]
Source: [PRD路径 / bug描述]

### Unit 1: [名称]
- [ ] Item 1 (§X.X): [具体规格]
```

**需求有歧义 → 停下来问用户。禁止猜测。**
**项目有 gate1_constitution 声明时，同步检查合规性。模板见 `constitution-template.md`。**

---

## 需求澄清机制

**触发条件**（任一即启动）：
- PRD 文字与原型图/流程图存在不一致
- 原型图中有关键细节无法确认（小字、模糊区域、连线条件）
- PRD 多处描述互相矛盾
- PRD 缺少必要细节但原型图/流程图中有所暗示
- P1 提取可验证项时发现歧义或不完整

### 澄清模式 A：结构化澄清（默认）

借鉴 Spec Kit `/speckit.clarify`，将歧义点转化为结构化多选题（反模式 #35：禁止跳过结构化澄清直接自行解读）。

**执行流程**：

1. P1 提取可验证项后，自动扫描所有可验证项，识别歧义点
2. 对每个歧义点生成结构化澄清问题：

```
## Clarification Round [N]

### Q1: [歧义点简述]
**来源**: [PRD §X.X / 图片路径]
**现状**: [当前理解]
**选项**:
- A. [方案 A] — [简述影响]
- B. [方案 B] — [简述影响]
- C. [方案 C] — [简述影响]
- D. 需要更多信息（请描述）
```

3. 用户逐题回答（选择字母或补充描述）
4. 将回答写入 `_clarifications.md`，格式：

```
## C[N]: [简述歧义点]
- **来源**: [PRD 章节 / 图片路径]
- **问题**: [具体歧义描述]
- **选项**: A. [方案A] / B. [方案B] / C. [方案C]
- **用户选择**: [字母] — [补充说明]
- **最终规格**: [可直接作为可验证项的确定性描述] (§C[N])
```

5. 可验证项中使用 `(§C[N])` 引用澄清来源

**结构化 vs 自由澄清**：

| 维度 | 结构化澄清（默认） | 自由澄清（兜底） |
|------|-------------------|-----------------|
| 适用场景 | 歧义有明确候选项（3-5 个） | 歧义开放，无明确候选项 |
| 用户负担 | 低（选字母） | 高（需要思考描述） |
| 记录完整性 | 高（选项+选择+理由） | 中（依赖用户表述） |

### 澄清模式 B：自由澄清（兜底）

保留原有自由流程，仅在结构化不适用时使用。

1. 在 PRD 目录下创建 `_clarifications.md`
2. 每条澄清记录格式：

```
## C[N]: [简述歧义点]
- **来源**: [PRD 章节 / 图片路径]
- **问题**: [具体歧义描述]
- **澄清**: [用户回答，逐字记录]
- **最终规格**: [可直接作为可验证项的确定性描述] (§C[N])
```

3. 可验证项中使用 `(§C[N])` 引用澄清来源
4. Plan 和验收清单中出现的澄清引用必须可追溯到 `_clarifications.md`

**禁止**：不记录澄清结果直接使用、口头确认不写文件、凭印象回忆澄清结论。

---

## P1.5：数据库调查（后端专属）

> 输出: `[qgw:gate1:P1.5] 数据库调查 ...` / `✅ N 张表, M 个枚举域已确认` 或 `⚠️ DB MCP 不可用, 跳过`

**引擎交互**（必须）：
- 开始前: `python gate-enforcer.py enter P1.5` → 收到 `ALLOW` 或 `SKIP`（SKIP 时直接跳过此步）
- 完成后: `python gate-enforcer.py complete P1.5`

**前置条件**：需求涉及后端开发（SQL/Mapper/Service）或数据库变更（Liquibase changelog/DML）。纯前端且无 DB 变更的需求跳过此步。

**`--opt` 模式不自动跳过 P1.5**：优化/重构涉及 DB 变更时仍需执行。判断依据不是模式参数，而是 P1 可验证项中是否包含 SQL/Mapper/Service/Liquibase 相关项。

**不可用时**：DB MCP 连接失败 → 输出警告并降级为仅代码/grep 分析。**禁止**因此阻塞 Gate 1 流程。降级时**必须**列出：
1. 受影响的具体验收项（如"列名验证"、"枚举值域确认"）
2. 替代验证手段（如 `grep -r "COLUMN_NAME" mapper/`、读取 Liquibase changelog）
3. 标记为 ⚠️ 降级项（Gate 2 S3.5 需补验）

### 执行步骤

**A. PRD 关键词 → 表名定位**

从 P1 提取的可验证项中，识别涉及的数据实体，定位数据库表。

> **项目特有映射**：各项目的 PRD 关键词与表名映射见项目自身文档（如项目 `.qgw/` 目录下的配置文件）。

定位方式：grep 代码中的表名引用 → 确认表存在。

**B. Schema 确认**

对计划中要引用的每张表，执行 `DESCRIBE` 或 `information_schema` 查询：

```
调查项：
1. 列是否存在（如 [目标表名] 是否有 [目标列名]）
2. 列类型和约束（NOT NULL、默认值）
3. 列注释（COMMENT）— 理解业务语义
4. 主外键关系 — 理解表间关联
```

示例 SQL：
```sql
DESCRIBE [目标表名];
-- 或
SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
FROM information_schema.COLUMNS
WHERE TABLE_NAME = '[目标表名]';
```

**C. 枚举值域确认**

对 PRD 中涉及枚举条件的字段，查询实际值域：

```sql
SELECT DISTINCT [枚举列名] FROM [目标表名];
-- 确认实际值覆盖 PRD 描述的所有类型
```

**D. 数据样例**

取 1-3 条真实数据理解实际结构和值：

```sql
SELECT * FROM [目标表名] LIMIT 3;
```

**E. 枚举完整性检查**

PRD 列出了 N 个枚举项（如 4 个角色、5 种类型），数据库必须有对应数据或列定义。PRD 列出的每一项都必须在调查结果中有对应条目。不允许用"不处理"、"默认"跳过任何 PRD 枚举项。

### 输出格式模板

调查结果写入计划文档的"数据库调查"章节：

```
## Database Investigation
Source: [需求路径]

### 表结构确认
| 表名 | 关键列 | 列存在 | 列注释 |
|------|--------|--------|--------|
| [表名] | [列名] | ✅/❌ | [列注释] |

### 枚举值域
| 字段 | PRD 描述 | 实际值 | 匹配 |
|------|---------|--------|------|
| [表名].[列名] | [PRD 描述的值] | [查询结果] | ✅/❌ |

### 数据样例
(关键样例数据摘要)

### 枚举完整性
PRD 列出 N 个 [类别]: [列举 PRD 的每一项]
→ 全部需在方案中逐个说明处理方式

### 验证 SQL（每项 DB 结论必备）

对每张表 / 每个列 / 每个枚举，列出可直接复制执行的可运行 SQL：

```sql
-- [验收项 ID] 验证 [表名].[列名] 大小写/类型/默认值
SHOW CREATE TABLE [表名];

-- [验收项 ID] 验证 [字段] 在 PRD 描述场景下的实际值
SELECT [列名], COUNT(*)
FROM [表名]
WHERE [业务条件]
GROUP BY [列名];

-- [验收项 ID] 验证两个候选字段是否一致（如 marks7 vs REVIEW_ACTUAL_TIME）
SELECT UUID, [字段A], [字段B],
  CASE WHEN IFNULL([字段A],'') != IFNULL([字段B],'') THEN '不一致' ELSE '一致' END AS diff
FROM [表名]
WHERE [业务条件]
LIMIT 10;
```

> **强制要求**：DB MCP 可用时，每条 SQL 必须实际执行并附结果摘要；不可用时 SQL 仍需列出，标 ⚠️ 待 Gate 2 S3.5 补验。仅文字描述"列存在"不算完成。
```

---

## P1.6：代码链路调查（所有需求必做）

> 输出: `[qgw:gate1:P1.6] 代码链路调查 ...` / `✅ N 个调用点, M 种分类, K 个补充项`

**引擎交互**（必须）：
- 开始前: `python gate-enforcer.py enter P1.6` → 收到 `ALLOW` 或 `SKIP`
- 完成后: `python gate-enforcer.py complete P1.6`

**适用范围**：所有需求（新增/替换/重构/修复），禁止跳过。"纯新增不需要调查"是错误判断——新增也需要匹配已有 pattern 和确认无冲突。

### A. 关键词 → 代码定位

从 P1 可验证项提取技术关键词（方法名、表名、组件名、业务术语），grep 所有涉及层。

**搜索范围**（按优先级）：
1. 项目 CLAUDE.md 中 `gate_search_paths` 声明的目录列表
2. 未声明时，自动检测项目根目录下的子目录（排除 node_modules、.git、target 等）

示例（某项目，以项目 dev-rule 基线仓库名为准）：
- `backend/` (后端, DDD-lite + CQRS)
- `legacy-backend/` (遗留后端, 传统 MVC)
- `frontend/` (前端)
- `viewer/` (浏览端前端)
- `mobile-h5/` (移动端前端)

每个调用点记录：层、文件:行号、调用内容。精确到行号，"大致位置"不算完成。

### B. 调用分类

将找到的调用点按用途分类：

| 类型 | 含义 | 示例 |
|------|------|------|
| 判断 | 权限/条件检查，影响流程走向 | `xxxAuth()`、`isOperation()` |
| 展示 | UI 渲染、标签、列表展示 | `showViewPermRole()`、列表列 |
| 写入 | 数据创建/更新/删除 | Service.save/update |
| 回调 | 外部系统回调处理 | `/api/callback`、`/webhook/xxx` |
| 配置 | 配置项/开关/枚举 | config_item、常量定义 |

每条标注状态：**需修改** 或 **需确认不受影响**。

### C. dev-rule Pattern 匹配

项目声明了 `dev_rule_path` 或 `gate_dev_rules` 时，读取 dev-rule 技能的 pattern 索引：

- 后端：`references/backend/patterns/*/index.md`
- 前端：`references/frontend/patterns/*/index.md`

为每个 unit 匹配最合适的架构模式，输出 pattern 名称和基线实例位置。未声明时跳过此步。

**配置优先级**：
1. `dev_rule_path`（推荐）：项目CLAUDE.md中声明的技能路径
2. `gate_dev_rules`（兼容旧方式）：项目CLAUDE.md中声明的技能名称

### D. 可验证项补充

将 P1.6 发现的、但 P1 未覆盖的调用点反馈到 P1：

- 输出 `[qgw:gate1:P1.6] ⚠️ 发现 K 个遗漏项，补充到 P1`
- 在 P1 可验证项列表中追加补充项，标注 `(P1.6 补充)`
- 无遗漏时输出 `[qgw:gate1:P1.6] ✅ P1 项已完整，无遗漏`

### 输出格式模板

调查结果写入计划文档的"代码链路调查"章节：

```
## Code Chain Investigation
Source: [需求路径]

### 调用点清单
| 层 | 文件:行号 | 调用类型 | 传入参数 | 期望值 | 状态 |
|----|----------|---------|---------|--------|------|
| 4.0 Service | ProcessServiceImpl.java:3362 | 展示 | taskId=Long | 返回 DTO | 需修改 |
| 4.0 Service | xxxAuth():L45 | 判断 | userId, role=String | boolean | 不受影响 |

> **传入参数列**：每个调用点必须列出关键参数的来源与类型。BUG 往往不在调用本身，而在传参（如 `formatIsOnTime(actual, plan)` 顺序反了、`detail.get("create_id")` 大小写不匹配、`marks7` vs `REVIEW_ACTUAL_TIME` 读写分离）。仅列文件:行号不足以暴露参数层 BUG。

### Pattern 匹配
| Unit | 推荐 Pattern | 基线实例 |
|------|-------------|---------|
| Unit 1 | query-list-api | ReportQueryController |

### P1 补充项
- [新增] V4.5: xxx 调用点需覆盖 (P1.6 补充)
```

---

## P1.7：PM 顾问评议

> 输出: `[qgw:gate1:P1.7] 派 PM 顾问评议可验证项 ...` / `✅ 0 ISSUE` 或 `⚠️ N ISSUE → 修 P1`

**引擎交互**（必须）：
- 开始前: `python gate-enforcer.py enter P1.7` → 收到 `ALLOW` 或 `SKIP`
- 完成后: `python gate-enforcer.py complete P1.7 --toolCallId "Agent|P1.7|ISO-timestamp"` → 引擎验证 toolCallId 格式

P1.6 完成后、P2 撰写 plan 前，派独立 PM 顾问子代理评议 P1 输出的可验证项列表。详细 prompt 模板见 `advisor-templates.md` 的 "P1.7 PM 顾问" 章节。

### 为什么需要 PM 顾问（不是 verifier）

P4 verifier 只能问"plan 是否覆盖 PRD §X.X"，无法问：
- "PRD §X.X 的表述是笔误还是业务原意？"
- "管理员可配置 ≠ 运行时实际执行"——配置 PASS 不等于实现 PASS
- "PRD 没说但业务必须的隐含需求"

主代理在 P1 提取可验证项时有**沉没成本**（已经读了 PRD、做了理解），倾向"自行解读"。PM 顾问无沉没成本，从产品视角独立判断。

### 评议维度

PM 顾问从 6 个维度评议，每项发现标记 ISSUE：

| 维度 | 问题示例 |
|------|---------|
| D1 PRD 笔误 vs 业务原意 | "跟进是否按时=检查实际<=检查计划" 自相矛盾 |
| D2 配置 PASS ≠ 实现 PASS | "邮件 8 封"只验配置存在，未验代码触发 |
| D3 PRD 文字 vs 原型图不一致 | 表头字段、按钮文案、流程节点 |
| D4 严重性预判 | SHOW_STOPPER / HIGH / MEDIUM / LOW |
| D5 隐含需求挖掘 | 错误路径、边界条件、权限审计 |
| D6 YAGNI 检查 | 功能是否真的需要？标准库能解决吗？原生平台特性能解决吗？ |

### YAGNI 检查清单（借鉴 Ponytail）

PM 顾问在评议时，必须检查以下 YAGNI 问题：

1. **这个功能真的需要吗？**
   - 是否有明确的业务需求？
   - 是否是推测性需求？
   - 如果删除，会影响核心业务吗？

2. **标准库能解决吗？**
   - 是否有现成的标准库函数？
   - 是否在重复造轮子？

3. **原生平台特性能解决吗？**
   - 是否有原生 API 可以使用？
   - 是否在使用第三方库做平台已经支持的事情？

4. **已安装的依赖能解决吗？**
   - 是否有已安装的依赖可以解决？
   - 是否需要新增依赖？

5. **能一行搞定吗？**
   - 是否可以用更简洁的方式实现？
   - 是否有过度抽象？

**YAGNI 发现示例**：
- `YAGNI-1`: 功能"自定义日期选择器"可以用原生 `<input type="date">` 替代
- `YAGNI-2`: 功能"邮箱验证"可以用标准库 `filter_var` 替代自定义正则
- `YAGNI-3`: 功能"缓存"可以用已安装的 `memcached` 替代自实现

### 主代理响应规则

PM 顾问输出 ISSUE 后，主代理**必须逐条响应**：

- **接受**：修订 P1 可验证项 + 标 §C[N] 澄清（如适用）+ 输出 `[qgw:gate1:P1.7] ✅ 接受 ISSUE PM-N，已修订 P1`
- **驳回**：必须给出技术理由 + 输出 `[qgw:gate1:P1.7] ⚠️ 驳回 ISSUE PM-N，理由：xxx`，由 P4 verifier 复核驳回合理性
- **YAGNI 接受**：如果 YAGNI 发现有效，简化需求 + 输出 `[qgw:gate1:P1.7] ✅ 接受 YAGNI-N，已简化需求`
- **YAGNI 驳回**：如果 YAGNI 发现不适用，必须说明为什么需要完整实现 + 输出 `[qgw:gate1:P1.7] ⚠️ 驳回 YAGNI-N，理由：xxx`

**禁止**：不响应、静默接受、模糊驳回（"主观认为不重要"不算理由）。

### 物证链

P1.7 完成后，验收清单 JSON 的 `verifierReports` 数组追加一条：
```json
{
  "round": "P1.7",
  "timestamp": "ISO 时间",
  "result": "PASS / ADVISE / BLOCK",
  "toolCallId": "Agent|P1.7|ISO 时间",
  "summary": "N ISSUE / M 隐含需求 / K YAGNI",
  "issues": ["PM-1", "PM-2"],
  "yagni": ["YAGNI-1", "YAGNI-2"]
}
```

### 跳过条件

仅以下可跳过（必须声明理由）：
- `--opt` 纯技术重构（无 PRD 变更）
- `--bug` 且 bug 描述明确无歧义（D1/D3 仍需检查）

跳过输出：`[qgw:gate1:P1.7] ⚠️ 跳过（理由：xxx）`

**禁止跳过**：`--prd` / `--all` 模式 + 任何含业务逻辑的需求。

---

## P1 出口检查点（进入 P2 前必须执行）

> 输出: `[qgw:gate1:P1-check] P1-check: P1.5={执行|跳过} P1.6={执行|跳过} P1.7={执行|跳过}`

**引擎交互**（必须）：
- `python gate-enforcer.py enter P1-check` → 引擎自动验证 P1.5/P1.6/P1.7 的决策状态（已执行=COMPLETED / 已跳过=SKIPPED+skip_reason）
- `python gate-enforcer.py complete P1-check` → 引擎写入 checkpoint

> 此步骤是虚拟步骤，不做语义工作，只做确定性 guard 聚合检查。
> 无此步骤的 complete = P1.5/P1.6/P1.7 被静默跳过，引擎会 BLOCK P2 的进入。

在进入 P2 前，**必须**输出此检查点日志。格式：

```
[qgw:gate1:P1-check] P1.5: {执行|跳过(理由)} | P1.6: {执行|跳过(理由)} | P1.7: {执行|跳过(理由)}
```

**跳过理由仅限以下**：
- P1.5 跳过: "纯前端需求，无 SQL/Mapper/Service/Liquibase 变更" 或 "--lite 模式"
- P1.6 跳过: "全新独立项目，无已有代码"（注意：在已有项目中纯新增功能**不能**跳过，必须匹配已有 pattern）或 "--lite 模式"
- P1.7 跳过: 仅 `--opt` 纯技术重构 或 `--bug` 且 bug 描述明确无歧义（D1/D3 仍需检查）或 "--lite 模式"

**`--opt` / `--bug` / `--prd` 模式均不自动跳过 P1.5 / P1.6 / P1.7**。判断依据是 P1 可验证项内容，不是模式参数。

**禁止**：无此日志直接进入 P2。缺少此日志 = P1.5/P1.6/P1.7 被静默跳过，违反 anti-pattern #12、#22、#25。

---

## P2：撰写/审查计划

> 输出: `[qgw:gate1:P2] 撰写计划 ...` / `✅ N 个 plan unit`

**引擎交互**（必须）：
- 开始前: `python gate-enforcer.py enter P2` → 必须收到 `ALLOW`（引擎检查 P1-check=COMPLETED）
- 完成后: `python gate-enforcer.py complete P2 --artifacts docs/plans/*.md`

### 分层文档结构

**重要**：Plan 必须采用分层文档结构，按需求层次拆分：

```
Feature（大需求）
├── Unit 1（小需求）→ 一个文件
│   ├── Task 1.1（任务）
│   ├── Task 1.2（任务）
│   └── Task 1.3（任务）
├── Unit 2（小需求）→ 一个文件
│   ├── Task 2.1（任务）
│   └── Task 2.2（任务）
└── ...
```

**拆分原则**：
- **Feature → Unit**：按业务模块拆分（数据库、后端接口、前端页面等）
- **Unit → Task**：按实现步骤拆分（创建表、插入数据、验证等）
- **Task 细节**：具体代码、验证方式、检查点

**目录结构**：
```
docs/plans/
├── {feature}-00-overview.md        # 总览：背景、目标、架构、依赖
├── {feature}-01-prd-summary.md     # PRD摘要：需求要点、业务规则
├── {feature}-02-architecture.md    # 架构设计：技术方案、模块划分
├── {feature}-03-unit1.md           # Unit 1 实现计划（含多个Task）
├── {feature}-04-unit2.md           # Unit 2 实现计划（含多个Task）
├── {feature}-05-unit3.md           # Unit 3 实现计划（含多个Task）
├── ...                             # 每个 Unit 一个文件
└── {feature}-99-acceptance.md      # 验收清单汇总
```

### 各文件职责

| 文件 | 职责 | 内容结构 |
|------|------|----------|
| **overview.md** | 背景、目标、架构、依赖关系、实现顺序 | 1-2页 |
| **prd-summary.md** | 需求要点、业务规则、边界条件、隐含需求 | 1-2页 |
| **architecture.md** | 技术方案、模块划分、接口设计、数据模型 | 2-3页 |
| **unit-N.md** | 单个Unit的实现计划，含多个Task | 按Task数量 |
| **acceptance.md** | 验收清单汇总（从verification聚合） | 1页 |

**Unit文件大小原则**：
- 小Unit（3-5个Task）：2-3KB
- 中Unit（6-10个Task）：4-6KB
- 大Unit（>10个Task）：考虑拆分为子Unit

### Unit 文件详细模板

每个 Unit 文件代表一个**小需求**，包含多个**任务**：

```markdown
# Unit N: [小需求名称]

> **Target**: [目标目录]
> **Reference**: [参考文档]
> **Pattern**: [使用的架构模式]
> **Status**: [当前状态]
> **Dependencies**: [依赖的其他Unit]
> **Task Count**: [任务数量]

## Scope

- **Allowed**: [允许变更的文件路径模式]
- **Forbidden**: [禁止变更的文件路径]
- **Estimated lines**: [预估变更行数]

## Task 列表

| Task | 名称 | 预估时间 | 状态 |
|------|------|----------|------|
| Task 1.1 | [任务名] | [时间] | [状态] |
| Task 1.2 | [任务名] | [时间] | [状态] |
| Task 1.3 | [任务名] | [时间] | [状态] |

## Task 1.1: [具体任务名]

**目标**: [要实现什么]

**实现方式**:
- [具体步骤1]
- [具体步骤2]

**关键代码**:
\`\`\`java
// 关键代码示例
\`\`\`

**依赖**:
- [依赖的文件/模块]

**检查点**:
- [ ] 检查项1
- [ ] 检查项2

## Task 1.2: [具体任务名]

... (重复上述结构)

## 可验证项

### V1.1 (§X.X): [验证项描述]

- **验证方式**: [如何验证]
- **预期结果**: [期望结果]
- **实际结果**: [实际结果 - Gate 2 填写]
- **状态**: [PASS/FAIL/PENDING]

### V1.2 (§X.X): [验证项描述]

...

## 风险点

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| [风险1] | [影响] | [缓解措施] |
| [风险2] | [影响] | [缓解措施] |

## 验证方式

\`\`\`bash
# 验证命令1
[命令]

# 验证命令2
[命令]
\`\`\`

## Gate 2 实现记录

> 以下内容由 Gate 2 填写

### 实际变更

| 文件 | 变更类型 | 行数 |
|------|----------|------|
| [文件路径] | [新增/修改/删除] | [行数] |

### 测试结果

| 测试项 | 结果 | 说明 |
|--------|------|------|
| [测试项] | [PASS/FAIL] | [说明] |
```

### 每个 plan unit 必须明确对应 P1 的每个可验证项（含 P1.6 补充项）。指定：
- **What**（映射到可验证项，包含 §X.X 和 §C[N] 引用）
- **Where**（文件路径、组件名，引用 P1.6 调用点清单的精确行号）
- **How**（方法，不过度具体）
- **Scope**（反模式 #37：每个 unit 必须声明变更范围）

### Scope 声明（Boundary Enforcement 基础）

每个 plan unit 必须声明变更范围，供 Gate 2 S2.5 boundary check 使用：

```markdown
## Plan Unit 1: [名称]

### Scope
- **Allowed**: [文件路径模式列表，如 src/views/**, src/components/Filter.tsx]
- **Forbidden**: [禁止变更的路径，如 src/utils/legacy.ts, src/api/unchanged-endpoint.ts]
- **Estimated lines**: [预估变更行数，如 150-200]
```

**路径模式规则**：
- 使用 glob 模式（`**` 匹配任意层级，`*` 匹配单层）
- Allowed 必须覆盖 P1.6 调用点清单中标记为"需修改"的所有文件
- Forbidden 列出不应被波及的文件（共享组件、其他 unit 的文件等）
- Estimated lines 用于 S2.5 检测 over-fixing（实际变更 > 2x 预估 → 警告）

**Dev-rule 模式选择**（项目声明了 `dev_rule_path` 或 `gate_dev_rules` 时）：
- 读取 dev-rule 技能的 patterns/ 索引（如 `references/backend/patterns/*/index.md`、`references/frontend/patterns/*/index.md`）
- 为每个 plan unit 指定使用的架构模式（如 "用 5.0-crud-module 模式"、"用 list-page + BaseFilterTable 模式"）
- Plan 中标注 pattern 名称和来源，确保 Gate 2 实现时有明确骨架可循
- 未声明时跳过此步

---

## P2.5：架构师顾问评议

> 输出: `[qgw:gate1:P2.5] 派架构师顾问评议 plan ...` / `✅ 0 ISSUE` 或 `⚠️ N ISSUE → 修 plan`

**引擎交互**（必须）：
- 开始前: `python gate-enforcer.py enter P2.5` → 收到 `ALLOW` 或 `SKIP`
- 完成后: `python gate-enforcer.py complete P2.5 --toolCallId "Agent|P2.5|ISO-timestamp"` → 引擎验证 toolCallId 格式

P2 撰写完 plan 后、P3 自验前，派独立架构师顾问子代理评议 plan 的架构合理性。详细 prompt 模板见 `advisor-templates.md` 的 "P2.5 架构师顾问" 章节。

### 为什么需要架构师顾问（不是 verifier）

P4 verifier 只能问"plan 是否覆盖可验证项"，无法问：
- "模式选型是仓促选最熟悉还是有更优 pattern？"
- "复用 marks-number 列模式是合理还是技术债？"
- "P0-1 修复该局部加 SQL 别名还是全局重构？"
- "改 SqlProvider 影响几个调用方？"

主代理在 P2 写 plan 时有**沉没成本**（已经选了模式、已经定了文件路径），倾向"按现有 pattern 改最小"。架构师顾问无沉没成本，从全局视角独立评估。

### 评议维度

架构师顾问从 6 个维度评议，每项发现标记 ISSUE：

| 维度 | 问题示例 |
|------|---------|
| A1 模式选型 | list-page vs 自造筛选区；crud-api vs 重复造轮子 |
| A2 技术债识别 | marks-number 列、双表架构主子查询不一致 |
| A3 局部 vs 全局修复 | 局部 SQL 别名（4h/低风险）vs 全局 SqlProvider 小写（2d/中风险）|
| A4 跨 unit 影响 | 改 SqlProvider 影响 N 个 findXxx 调用方 |
| A5 严重性校准 | Popconfirm 基线 0 用 ≠ 禁用 API，PM 标 P0 应降 P1 |
| A6 修复策略推荐 | 方案 A vs 方案 B + 工作量 + 风险 + 推荐理由 |

### 主代理响应规则

架构师顾问输出 ISSUE 后，主代理**必须逐条响应**：

- **接受**：修订 plan + 输出 `[qgw:gate1:P2.5] ✅ 接受 ISSUE ARCH-N，已修订 plan`
- **驳回**：必须给出技术理由 + 输出 `[qgw:gate2:P2.5] ⚠️ 驳回 ISSUE ARCH-N，理由：xxx`，由 P4 verifier 复核

**A3（局部 vs 全局）必须决策**：不能"先记下来下个 sprint 处理"。如果选择"接受技术债"，必须在 plan 中明确**接受理由 + 跟踪机制**。

### 根因簇归并

架构师顾问必须将多个 ISSUE 归并为根因簇（同根因 ≥3 项 → 升级 dev_rule 建议）。输出格式：

```
- Cluster X：[根因描述] → 包含 ISSUE: ARCH-1, ARCH-3, ARCH-5
- Cluster Y：...
```

### 物证链

P2.5 完成后，验收清单 JSON 的 `verifierReports` 数组追加一条：
```json
{
  "round": "P2.5",
  "timestamp": "ISO 时间",
  "result": "PASS / ADVISE / BLOCK",
  "toolCallId": "Agent|P2.5|ISO 时间",
  "summary": "N ISSUE / M 根因簇",
  "issues": ["ARCH-1", "ARCH-2"],
  "clusters": ["Cluster X"]
}
```

### 跳过条件

仅以下可跳过（必须声明理由）：
- plan 仅含 1 个 unit 且无跨文件改动
- 纯文案/样式调整（无架构决策）
- `--debug` bug 修复且修复范围 ≤ 10 行

跳过输出：`[qgw:gate1:P2.5] ⚠️ 跳过（理由：xxx）`

**禁止跳过**：
- 任何涉及 SqlProvider / Mapper / DTO / 共享组件的修改
- 任何 ≥ 2 个 unit 的 plan
- 任何含"修复策略选择"的 plan

---

## P3：自验计划完整性

> 输出: `[qgw:gate1:P3] 自验计划完整性 ...` / `✅ 全部覆盖` 或 `❌ N 项缺口 → 修复中`

**引擎交互**（必须）：
- 开始前: `python gate-enforcer.py enter P3`
- 完成后: `python gate-enforcer.py complete P3`

逐条检查：
- **Covered**：引用可验证项 + 引用 plan 章节 + 确认匹配
- **Missing**：引用可验证项 + plan 中应出现的位置
- **Ambiguous**：引用可验证项 + 引用 plan + 说明差距

额外检查 P1.6 调用点清单中标记为"需修改"的调用点是否全部被 plan 覆盖。遗漏 → Missing。

修复所有缺口后进入 P4。

---

## P4：独立 verifier 子代理

> 输出: `[qgw:gate1:P4] 派独立 verifier 子代理 (round N)` / `✅ 全部 COVERED` 或 `❌ N 项 MISSING → 修 plan → 重验`

**引擎交互**（必须）：
- 开始前: `python gate-enforcer.py enter P4`
- 完成后: `python gate-enforcer.py complete P4 --toolCallId "Agent|P4|ISO-timestamp"` → **引擎强制检查 toolCallId 非空且格式有效**，否则 BLOCK
- 失败时: `python gate-enforcer.py fail P4 --reason "..." --rootCause CODE|PLAN`

自验 100% 通过后，派子代理独立验证。详细 prompt 模板见 `verifier-templates.md`。

**硬性要求：必须通过 `Task` 或 `Agent` 工具调用派发子代理。禁止仅输出日志文本而不实际派发。**

子代理 prompt 必须包含：
1. 可验证项（P1 提取的，含 P1.6 补充项）
2. 需求文档位置
3. Plan 文档位置
4. 指令：逐项报告 COVERED / MISSING / PARTIAL + 证据
5. **Dev-rule 模式覆盖检查**（如果项目声明了 `dev_rule_path` 或 `gate_dev_rules`）：verifier 检查每个 plan unit 是否指定了正确的架构模式，模式选择是否符合 dev-rule 的 patterns 索引推荐
6. **完整性抽查**：verifier 从 PRD 中独立提取 2-3 个技术关键词，grep 代码库找到对应调用点，检查这些调用点是否被 Plan 覆盖。未覆盖 → MISSING（不等 P1 的可验证项列表）

**派发自检**：P4 完成后、进入 P5 前，确认本步骤确实产生了 `Task` 或 `Agent` 工具调用。如果工具调用失败（权限拒绝、子代理报错），输出 `[qgw:gate1:P4] ❌ 子代理派发失败` 并报告用户，禁止静默跳过。

**物证链写入**：verifier 验证后（无论 PASS 或 FAIL），将本次工具调用记录写入验收清单 JSON：

1. 在 `verifierReports` 数组中追加一条记录，包含 `round`、`timestamp`、`result`、`toolCallId`
2. `toolCallId` 格式：`"Agent|round{N}|{ISO-timestamp}"`（如 `"Agent|round2|2026-06-10T21:15:00"`）。禁止纯描述占位符（如 `"verifier"`、`"round1"`）。**禁止使用 `"main|"` 前缀**——P4 的 Writer≠Verifier 原则要求必须是独立子代理派发，主代理自验不算 P4 执行
3. `result` 为 FAIL 时，`failItems` 必须列出具体失败项 ID（如 `["V2.3", "V2.4"]`），禁止空数组
4. 在每个 PASS 的 item 下设置 `toolCallId` 为本次 toolCallId 值
5. 输出 `[qgw:gate1:P4] ✅ 物证链已写入: {toolCallId}`
6. **FAIL 或 PARTIAL 后触发 evolve**：首次 FAIL/PARTIAL 后立即创建 `docs/verification/error-patterns.json`，记录根因分类（CODE/PLAN）。不等 Unit 完成
7. **无 toolCallId → 校验不通过，禁止进入 P5**

> `toolCallId` 防止代理仅输出日志文本冒充 P4 执行。`--self` 自检时交叉验证 JSONL 中的实际 Agent/Task 工具调用。

---

## P5：通过 → 移交 Gate 2

> 输出: `[qgw:gate1:P5] → 验收清单持久化 → 移交 Gate 2`

**引擎交互**（必须）：
- 开始前: `python gate-enforcer.py enter P5` → 引擎检查 P4=COMPLETED 且 toolCallId 存在
- 完成后: `python gate-enforcer.py complete P5` → 引擎验证 verification JSON 存在、QGW-INDEX 已更新、session summary 已写入

验收清单追加到 Plan 文档末尾（持久化，防止 context compaction 丢失），同时更新结构化 JSON。

**步骤 A：写入验收 JSON**（必须，使用 `Write` 工具）

将结构化验收数据写入 `docs/verification/unit-{N}.json`。文件不存在则创建：

```json
{
  "unit": "Unit 1: 名称",
  "source": "需求路径",
  "generated": "日期",
  "items": [
    { "id": "A1.1", "ref": "§X.X", "spec": "具体规格", "status": "PENDING", "toolCallId": null }
  ],
  "verifierReports": [],
  "feedbackRounds": 0,
  "maxFeedbackRounds": 2
}
```

如存在 `_clarifications.md`，JSON 顶层添加 `"clarifications": "PRD目录/_clarifications.md"`。

**步骤 B：追加到 Plan 文档末尾**（Markdown 格式）

```
<!-- Appended by quality-gate-workflow Gate 1 -->
## Acceptance Criteria Checklist
Source: [需求路径]
Clarifications: [PRD目录/_clarifications.md 或 "无"]
Generated: [日期]
Version: 1.1
FeedbackRounds: 0
MaxFeedbackRounds: 2

### Unit 1: [名称]
- [ ] Item 1 (§X.X): [规格]
- [ ] Item 2 (§C1): [澄清后的规格]
```

> 每个 item 的 `toolCallId` 在 verifier 通过后由 P4 步骤写入。提交前 Hook 脚本会检查此字段。

**步骤 C：更新 Master Index**

在 `docs/QGW-INDEX.md` 中：
1. 更新 Active Sessions 表：status → COMPLETED，填写 Verification 列
2. 追加 Document Registry 行：Plan（v1.0）+ Verification

**步骤 D：写入 Session Summary**（必须，使用 `Write` 工具）

在 `docs/sessions/{session-id}.md` 写入完整 session summary，格式见 SKILL.md "Session Summary" 章节。包含：
- Execution Flow：每个步骤的 Status + Notes
- Decisions：跳过的步骤及理由、顾问 ISSUE 响应
- Traceability：验收项 → 代码变更 → commit（如适用）
- Bug Log：S4 中发现并修复的 BUG（如适用）

**步骤 E：更新 Session Registry**

在 `docs/sessions/INDEX.md` 追加当前 session 行（如文件不存在则创建）。

**步骤 F：Git Trailer 生成**（反模式 #40）

Gate 1 产出 Plan 后如需提交（如创建 PR 或分支），在 commit message 末尾追加 QGW trailer：

```
QGW-Gate: gate1
QGW-Status: planned
QGW-Plan: {plan 文件路径}
QGW-Session: {session-id}
QGW-Items: {item_count} items
```

**移交内容**：
- Plan 文档（含验收清单附录）
- 结构化 JSON（`docs/verification/unit-*.json`）
- 澄清文件（如存在 `_clarifications.md`，verifier 需能引用 §C[N]）
- Master Index（`docs/QGW-INDEX.md`）
- Session Summary（`docs/sessions/{session-id}.md`）

**P5 自检**：
1. 确认 `docs/verification/unit-*.json` 文件已实际存在。文件不存在 = P5 未完成，禁止移交 Gate 2。
2. 确认 `docs/QGW-INDEX.md` 已更新。未更新 = 反模式 #28。
3. 确认 `docs/sessions/{session-id}.md` 已写入。未写入 = 反模式 #29。

---

## Bug 模式

**P1-Bug**：提取 bug 症状 + 预期行为 + 影响范围 + 根因假设

**P2-Bug**：确认根因 + 修复方案 + 涉及文件 + 回归风险

然后 P3→P4→P5 同主流程。

---

## Optimization 模式

**P1-Opt**：提取当前状态 + 目标状态 + 约束条件 + 衡量指标

然后 P2→P3→P4→P5 同主流程。

---

## 反馈回路

> 输出: `[qgw:feedback] Gate 2 发现 PLAN 根因 → 反馈 Gate 1` / `Gate 1 修 plan → 重验 → 回到 Gate 2`

```
Gate 2 verifier 发现 PLAN 根因
    ↓
1. 在 Plan 文档中定位问题段落
2. 修改 Plan 内容 + 追加 QGW-VERSION 行（记录原因）
3. 同步更新 docs/verification/unit-{N}.json 中受影响的 item（status 重置为 PENDING）
4. 更新 docs/QGW-INDEX.md 中 Plan 版本号
5. 在 session summary 的 Decisions 表追加记录
6. 反馈回 Gate 1 P3→P4 重验
    ↓
feedbackRounds 递增（写入验收清单 JSON）
    ↓
feedbackRounds >= maxFeedbackRounds (默认2)?
    ├─ 否 → 继续
    └─ 是 → 停下来交给用户
```

**Plan 文档修改规则**：
- **不覆盖原文** — 在问题段落下方追加修正说明 + `QGW-VERSION` 标记（反模式 #32）
- **已通过的 unit 不受影响** — 只修有 PLAN 根因的 unit
- **验收清单 JSON 重置受影响 item 的 status 为 PENDING**
- **版本标记格式**：`<!-- QGW-VERSION: vX.X | {timestamp} | reason: feedback round N — {描述} -->`

**Round 计数器机制**：
- 验收清单 JSON 的 `feedbackRounds` 字段记录 PLAN 根因反馈循环次数（默认 0）
- 每次 PLAN 根因触发反馈回路时，`feedbackRounds += 1`
- 当 `feedbackRounds >= maxFeedbackRounds`（默认 2）时，**强制停止**，输出 `[qgw:feedback] ❌ 已达最大反馈轮次 ({maxFeedbackRounds}) — 停止并交由用户决策`
- `maxFeedbackRounds` 可在验收清单 JSON 中配置（最小 1，默认 2）
- 新增一轮前输出 `[qgw:feedback] 🔄 反馈轮次 {round}/{maxFeedbackRounds}`
