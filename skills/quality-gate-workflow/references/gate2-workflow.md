# Gate 2 工作流详细步骤

> 日志格式规范、平台标识、状态图标、复盘路径 → 见 SKILL.md "进度输出" 章节（唯一定义处）。

## 目录
- Step 0：工作空间初始化
- Step 1：提取验收标准
- Step 2：实现
- Step 3：自验
- Step 3.5：数据库 Schema 验证
- Step 4：独立 verifier 子代理
- Step 5：100% 通过 → 提交
- Audit 模式
- Debug 模式
- Compaction Recovery
- 全链路复盘

---

## Step 0：工作空间初始化

> 输出: `[qgw:gate2:S0] 工作空间检查 ...` / `✅ 目录就绪` 或 `✅ 已创建`

**引擎交互**（必须）：
- 开始前: `python gate-enforcer.py enter S0` → 必须收到 `ALLOW`
- 完成后: `python gate-enforcer.py complete S0`

检查并创建工作空间目录（如果不存在）：

```bash
mkdir -p docs/plans docs/verification docs/reports docs/sessions
```

检查结果：
- `docs/verification/` 存在 → ✅
- `docs/verification/` 不存在 → 创建并输出 `[qgw:gate2:S0] ✅ 已创建 docs/verification/`
- 同理处理 `docs/plans/`、`docs/reports/`、`docs/sessions/`

### Master Index 初始化

检查 `docs/QGW-INDEX.md` 是否存在：
- 不存在 → 创建初始 INDEX，注册当前 session 行（status=IN_PROGRESS）
- 已存在 → 追加当前 session 行

### Session 注册

在 `docs/QGW-INDEX.md` 的 Active Sessions 表追加：

```
| {session-id} | {date} | gate2 | IN_PROGRESS | {plan-file} | — | — |
```

### PRD diff 检测

Gate 2 S0 开始时，检查 PRD 文件修改时间 vs Gate 1 完成时间（从 Plan 文档的 Generated 字段获取）：
1. 如 PRD 有修改 → 输出 `[qgw:gate2:S0] ⚠️ PRD 文件自 Gate 1 后有修改`
2. 列出受影响的章节 → 标记对应可验证项为 NEEDS_REVIEW
3. 询问用户：增量更新（仅处理变更部分）或继续 Gate 2（记录 decision）

**禁止**：因目录不存在而跳过 JSON 写入（验收数据、error-patterns）。目录缺失必须先创建再继续。

---

## Step 1：提取验收标准

> 输出: `[qgw:gate2:S1] 提取验收标准 (来自 Gate 1 清单 / 手动提取)` / `✅ N 条标准`

**引擎交互**（必须）：
- 开始前: `python gate-enforcer.py enter S1`
- 完成后: `python gate-enforcer.py complete S1`

**优先从 Gate 1 验收清单读取**（Plan 文档附录 + 结构化 JSON）。存在时直接使用，不重复提取。

**手动提取**（无 Gate 1 时）：重读 Plan 文档 AND 源需求文档。每条标准必须具体可验证：

- 组件类型：写明具体组件（如"流程树多选组件"），禁止"有筛选器"
- 字段存在：写明具体字段有无（如"跟进人页面无审核人字段"），禁止"字段正确"
- 标签文本：写明确切文本（如"列标题='引发何种不良后果'"），禁止"列名正确"

```
## Acceptance Criteria: [Unit名称]
Source: [plan路径] + [spec路径]

- [ ] Field "流程": component = ProcessTreeSelector (multi)
- [ ] "计划完成时间": required = configurable

Dev Rule Checklist: [项目 CLAUDE.md dev_rule_path 或 gate_dev_rules]
- [ ] (项目专属编码规范项)
```

---

## Step 2：实现

> 输出: `[qgw:gate2:S2] 实现 Unit N/M: [名称] ...`

**引擎交互**（必须）：
- 开始前: `python gate-enforcer.py enter S2`
- 完成后: `python gate-enforcer.py complete S2`

按验收标准写代码。

**读取 Scope**：实现前从 Plan 中读取当前 unit 的 Scope 声明（`allowedChanges` / `forbiddenChanges` / `estimatedLines`）。实现过程中只修改 allowed 路径内的文件，禁止修改 forbidden 路径内的文件。

**Dev-rule 代码骨架**（项目声明了 `dev_rule` / `dev_rule_path` / `gate_dev_rules` 且 Plan 指定了 pattern 时）：

1. 先读取 `.qgw/config.json` 的 `dev_rule.path`/SKILL.md（项目自生活规范）
2. 再读取 `reference_skills` 中 `role=pattern_source` 的技能（参考技能）
3. 读取 Plan 中标注的 pattern 文件（如 `references/backend/patterns/backend-5.0-pattern/crud-api.md`）
4. 以 pattern 中的代码骨架为模板实现，保持架构一致
5. 同时读取 dev-rule 的 rules（如 Track-5.0 rules-5.0/ 或前端 rules/），遵循编码规范

**优先级解析**：project-dev-rule 核心规则 > reference_skills 规则 > 通用规范（冲突时以项目经验结晶为准）。

未声明任何 dev-rule 配置或 Plan 未指定 pattern 时，按常规实现。

---

## Step 2.5：Boundary Check

> 输出: `[qgw:gate2:S2.5] Boundary Check ...` / `✅ 所有变更在允许范围内` 或 `❌ N 处越界变更`

**引擎交互**（必须）：
- 开始前: `python gate-enforcer.py enter S2.5`
- 完成后: `python gate-enforcer.py complete S2.5`

借鉴 agent-spec 的 boundary enforcement，检查代码变更是否在 Plan 定义的范围内（反模式 #36：越界变更必须回滚或更新 Plan）。

**执行步骤**：

1. 获取本次变更文件列表：
   ```bash
   git diff --name-only HEAD~1  # 或 git diff --staged --name-only
   ```

2. 对照 Plan 中当前 unit 的 `allowedChanges` 路径模式：
   - 每个变更文件必须匹配至少一个 allowed 模式
   - 不匹配 → 标记为越界

3. 检查 `forbiddenChanges`：
   - 变更文件匹配任何 forbidden 模式 → 标记为禁止

4. 检查变更行数（可选，有 `estimatedLines` 时）：
   - 实际变更行数 > 2x 预估 → 输出警告（不阻断，但记录）

5. 输出结果：

**通过时**：
```
[qgw:gate2:S2.5] Boundary Check ...
  Allowed: [src/views/**, src/components/Filter.tsx]
  Actual changes: src/views/ProcessTrack/index.tsx, src/components/Filter.tsx
  ✅ 所有变更在允许范围内 (2 文件, ~120 行)
```

**越界时**：
```
[qgw:gate2:S2.5] Boundary Check ...
  Allowed: [src/views/**]
  Actual changes: src/views/ProcessTrack/index.tsx, src/utils/legacy.ts
  ❌ src/utils/legacy.ts 不在 allowedChanges 中
  → 选项 A: 回滚 src/utils/legacy.ts 的变更
  → 选项 B: 更新 Plan 的 allowedChanges 后重走 S2
```

**禁止**：越界变更不处理直接继续 S3。boundary check 失败必须先解决再进入自验。

---

## Step 3：自验

> 输出: `[qgw:gate2:S3] 自验 ...` / `✅ 全部通过` 或 `❌ N 项 Fail → 修复中`

**引擎交互**（必须）：
- 开始前: `python gate-enforcer.py enter S3`
- 完成后: `python gate-enforcer.py complete S3`

逐条检查每条标准：

- **Pass**：引用标准 + 引用代码 + 确认匹配
- **Fail**：引用标准 + 引用代码 + 说明偏差

修复所有 Fail 后进入 Step 3.5。

---

## Step 3.5：数据库 Schema 验证（后端专属）

> 输出: `[qgw:gate2:S3.5] Schema 验证 ...` / `✅ N 处 SQL 列名已确认` 或 `❌ M 处列不存在 → 修复中` 或 `⚠️ DB MCP 不可用, 跳过`

**引擎交互**（必须）：
- 开始前: `python gate-enforcer.py enter S3.5` → 收到 `ALLOW` 或 `SKIP`
- 完成后: `python gate-enforcer.py complete S3.5`

**前置条件**：本次实现涉及 SQL 拼接（SqlProvider、Mapper XML、动态 SQL）。纯前端实现跳过此步。

**不可用时**：DB MCP 连接失败 → 降级为仅静态 grep 分析。降级时**必须**列出：受影响的 SQL 列名 + 替代验证手段（grep Mapper XML / Liquibase changelog 交叉确认）+ 标记 ⚠️。

### 执行步骤

**A. 提取代码中引用的列名**

从本次改动的 SqlProvider / Mapper 代码中，提取所有 `<alias>.<column>` 形式的列名引用：

```
代码: "t.flow_id" → alias=t, column=flow_id
代码: "r.dept_id" → alias=r, column=dept_id
```

**B. 确认 alias 对应的实际表**

从 SQL 上下文追踪 alias → FROM/JOIN 的目标表：

```
"FROM order_table t" → t = order_table
"JOIN department d" → d = department
```

**C. DESCRIBE 验证列存在**

对每个 (表, 列) 对，执行：

```sql
SHOW COLUMNS FROM <表名> LIKE '<列名>';
-- 或
SELECT COLUMN_NAME FROM information_schema.COLUMNS
WHERE TABLE_NAME = '<表名>' AND COLUMN_NAME = '<列名>';
```

结果为空 → **列不存在** → 立即修复。

**D. 过滤方法匹配验证**

验证过滤方法与目标表类型匹配。确认代码中调用的过滤/查询方法适用于其实际操作的目标表，避免方法与表类型交叉误用。

**E. Map key 格式验证**

对 MyBatis 原生查询返回的 Map，验证取值 key 的大小写：

```sql
-- 执行实际查询取 1 条，观察返回 Map 的 key 格式
SELECT TYPE, ITEM_ID FROM some_table LIMIT 1;
→ 确认 key 是大写 TYPE/ITEM_ID 还是小写 type/item_id
```

---

## Step 4：独立 verifier 子代理

> 输出: `[qgw:gate2:S4] 派独立 verifier 子代理 (round N)` / `✅ 全部 PASS` 或 `❌ N 项 FAIL — 根因: CODE / PLAN`

**引擎**: `enter S4` → [语义工作：派子代理验证] → `complete S4 --toolCallId "Agent|S4|ISO-timestamp"` → 引擎强制校验格式，否则 BLOCK。失败时: `fail S4 --reason "..." --rootCause CODE|PLAN`

详细 prompt 模板见 `references/verifier-templates.md`。**必须通过 Task/Agent 工具派发子代理**，禁止仅输出日志。子代理 prompt 必须包含：
1. 验收标准 + 需求/代码位置
2. 逐项报告 PASS/FAIL + 证据 + Code Refs
3. Dev rule 合规检查（如有）
4. 数据库 Schema 抽检（后端，不可用时 SKIP）

物证链写入：将 `toolCallId`（格式由引擎校验）写入 `verifierReports` 和每个 PASS item 的 `codeRefs`。FAIL 时 `failItems` 必须列出具体 ID。FAIL/PARTIAL 后触发 evolve + BUG 记录。无 toolCallId → 引擎禁止进入 S5。

**根因分类**：

- **CODE**：Plan 正确，代码没照做 → Gate 2 内修，收敛 ≤2 轮
- **PLAN**：Plan 本身没对齐需求 → 反馈 Gate 1，硬顶 1 轮

### S4 增量模式（`--incremental`）

当用户指定 `--incremental` 时，S4 切换为增量验证模式（反模式 #38：首次 Gate 2 不可增量，#39：boundary check 不可跳过）。

**前置条件**：
- 必须有已有的 verification JSON（至少一个 unit 已通过 S5）
- 必须有 git 历史（能获取 diff）
- 不适用于 `--debug`（无 Plan 的场景）

**增量验证流程**：

1. 获取变更文件列表：
   ```bash
   git diff --name-only HEAD~1  # 或 git diff --staged --name-only
   ```

2. 从已有 verification JSON 的 `codeRefs` 中，找到引用了变更文件的 item：
   ```
   变更文件: src/views/ProcessTrack/index.tsx, src/components/Filter.tsx
   → codeRefs 引用这些文件的 item: U1-01, U1-02, U1-05
   ```

3. 从 Plan 的 `allowedChanges` 中，找到覆盖变更文件的 unit

4. 只验证受影响的 item（标记为 PENDING → PASS/FAIL）

5. 其余 item 标记为 SKIPPED：
   ```json
   {
     "id": "U1-03",
     "status": "SKIPPED",
     "skipReason": "incremental: 未变更 codeRefs 涉及的文件"
   }
   ```

**增量 verifier 输出格式**：

```
[qgw:gate2:S4'] 增量验证 ...
  变更文件: src/views/ProcessTrack/index.tsx, src/components/Filter.tsx
  受影响 item: U1-01 (§6.1.1), U1-02 (§6.1.2), U1-05 (§6.1.5)
  跳过 item: U1-03, U1-04, U1-06-U1-12 (未变更)
  → 验证 3 项, 跳过 9 项
```

验证后：
```
[qgw:gate2:S4'] 增量验证完成 ...
  PASS: 3 项 (U1-01, U1-02, U1-05)
  SKIPPED: 9 项
  ✅ 增量验证通过
```

**SKIPPED 项处理**：
- SKIPPED 不算 PASS 也不算 FAIL
- 不计入通过率
- Hook 对 SKIPPED 项输出警告但不阻止提交
- 下次全量验证时重新验证

---

## Step 4.5：E2E Behavior Check（`--e2e`）

> 输出: `[qgw:gate2:S4.5] E2E 行为验证 ...` / `✅ 测试全部通过` 或 `❌ N 个测试失败`

**引擎交互**（必须）：
- 开始前: `python gate-enforcer.py enter S4.5` → 收到 `ALLOW` 或 `SKIP`（init 时未指定 `--e2e` 则自动 SKIP）
- 完成后: `python gate-enforcer.py complete S4.5`

借鉴 Autonoma 的 agentic testing，S4 验证"代码匹配 Plan"（静态），S4.5 验证"代码正确运行"（动态）。反模式 #45：E2E 不可替代 S4。

**前置条件**：用户指定 `--e2e` 参数。未指定时跳过此步。

**执行步骤**：

1. **检测测试框架**（优先级：`.qgw/config.json` > 自动检测）：

   ```bash
   # 检查 .qgw/config.json
   cat .qgw/config.json | grep "e2e"

   # 自动检测
   ls package.json && node -e "const p=require('./package.json'); console.log(p.scripts?.test)"
   ls pom.xml && echo "maven"
   ls playwright.config.ts && echo "playwright"
   ```

2. **执行测试**：

   ```bash
   # npm/jest/vitest
   npm test

   # Maven
   mvn test

   # pytest
   pytest

   # 自定义命令（从 .qgw/config.json）
   {command}
   ```

3. **解析结果**：
   - 全部通过 → PASS
   - 有失败 → FAIL + 列出失败用例
   - 无测试文件 → SKIP + 警告

4. **输出示例**：

**通过时**：
```
[qgw:gate2:S4.5] E2E 行为验证 ...
  框架: jest (检测到 package.json)
  执行: npm test
  结果: 45 passed, 0 failed
  ✅ E2E 验证通过
```

**失败时**：
```
[qgw:gate2:S4.5] E2E 行为验证 ...
  框架: jest (检测到 package.json)
  执行: npm test
  结果: 45 passed, 2 failed
  失败用例:
    - test/ProcessTrack.test.ts:42 — "筛选器应支持多选"
    - test/ProcessTrack.test.ts:58 — "责任部门字段应显示 dutyDeptName"
  ❌ E2E 验证失败 — 返回 S2 修复
```

**无测试时**：
```
[qgw:gate2:S4.5] E2E 行为验证 ...
  ⚠️ 未检测到测试文件，跳过 E2E 验证
  建议：添加测试以提高代码质量保证
```

**E2E 失败处理**：
- 返回 S2 修复失败的测试
- 收敛 ≤2 轮（与 S4 CODE 根因一致）
- 超过 2 轮 → 停止并交由用户决策

**E2E 结果写入 verification JSON**：
```json
{
  "e2eResult": {
    "framework": "jest",
    "command": "npm test",
    "passed": 45,
    "failed": 2,
    "skipped": 0,
    "failedTests": ["test/ProcessTrack.test.ts:42"],
    "timestamp": "2026-06-16T12:00:00Z"
  }
}
```

---

## Step 5：100% 通过 → 提交

> 输出: `[qgw][{timestamp}][{platform}:{session_id}][gate2][S5/5] ✅ Unit N/M 提交`

**引擎**: `enter S5` → 引擎检查 S4=COMPLETED 且 toolCallId 存在 → [语义工作：写入 verification JSON + commitSha + Git Trailer + 更新 Plan/Index/Session] → `complete S5` → 引擎验证 toolCallId 完整、codeRefs 存在、Plan 已更新

> 引擎 `complete S5` 自动检查：物证链完整性、Plan 同步、codeRefs 存在、session summary 写入。不满足则 BLOCK。

**提交顺序**：先验证再提交。验证结果写入 `docs/verification/unit-{N}.json`。提交后写入 `commitSha`。

**Git Trailer**（反模式 #40）：提交时追加 QGW trailer：

```
QGW-Gate: gate2
QGW-Status: verified
QGW-Plan: {plan 文件路径}
QGW-Session: {session-id}
QGW-Items: {pass_count}/{total_count} PASS
QGW-Mode: {full|incremental}
```

增量模式时额外显示 SKIPPED 数量：
```
QGW-Mode: incremental
QGW-Items: 3/12 PASS, 9 SKIPPED
```

**步骤 A：更新 Master Index**

在 `docs/QGW-INDEX.md` 中：
1. 更新 Active Sessions 行：status → COMPLETED，填写 Report 列
2. 追加 Document Registry 行：Report

**步骤 B：写入 Session Summary**（必须，使用 `Write` 工具）

在 `docs/sessions/{session-id}.md` 写入完整 session summary，格式见 SKILL.md "Session Summary" 章节。包含：
- Execution Flow：每个步骤的 Status + Notes
- Decisions：跳过的步骤及理由、顾问 ISSUE 响应
- Traceability：验收项 → codeRefs → commitSha
- Bug Log：S4 中发现并修复的 BUG（每轮 S4 修复都记录 BUG ID + 类型 + 根因 + 修复描述）

**步骤 C：自动生成 Audit Report**（如有）

如使用 `--audit` 模式，使用 `assets/report-templates.md` 模板，用 `Write` 工具写入 `docs/reports/{plan-name}-report-{date}.md`。

**步骤 D：更新 Session Registry**

在 `docs/sessions/INDEX.md` 追加当前 session 行（如文件不存在则创建）。

**步骤 E：更新 Plan 文档（必须）**

**重要**：Gate 2 完成后，**必须**更新对应的 Plan 文档，实现全生命周期闭环。

更新 `docs/plans/{feature}-0{N}-unit{N}.md` 中的以下内容：

1. **Task 状态更新**：
   ```markdown
   | Task | 名称 | 预估时间 | 状态 |
   |------|------|----------|------|
   | Task 1.1 | 创建积分流水表 | 30min | ✅ 完成 |
   | Task 1.2 | 创建勋章表 | 20min | ✅ 完成 |
   ```

2. **可验证项状态更新**：
   ```markdown
   ### V1.1 (§5.1): 积分流水表字段齐全
   
   - **验证方式**: `DESCRIBE _honor_point_ledger;`
   - **预期结果**: 27 个字段，类型正确
   - **实际结果**: ✅ 27 字段，类型正确
   - **状态**: PASS
   ```

3. **Gate 2 实现记录更新**：
   ```markdown
   ## Gate 2 实现记录
   
   > 以下内容由 Gate 2 填写
   
   ### 实际变更
   
   | 文件 | 变更类型 | 行数 |
   |------|----------|------|
   | honor-point-ledger.xml | 新增 | 85 |
   | honor-medal.xml | 新增 | 45 |
   
   ### 测试结果
   
   | 测试项 | 结果 | 说明 |
   |--------|------|------|
   | Liquibase 更新 | PASS | 3 表创建成功 |
   | 配置项插入 | PASS | 3 条配置项可见 |
   ```

**S5 自检**：
1. 确认 `docs/verification/unit-*.json` 文件已实际存在。文件不存在 = S5 未完成。
2. 确认 `docs/QGW-INDEX.md` 已更新。未更新 = 反模式 #28。
3. 确认 `docs/sessions/{session-id}.md` 已写入。未写入 = 反模式 #29。
4. 确认 PASS 项的 `codeRefs` 和 `commitSha` 已写入。未写入 = 反模式 #30。
5. **确认 Plan 文档已更新**。未更新 = 反模式 #31（全生命周期闭环断裂）。

---

## S5-evolve：Dev-Rule 进化检查

> 输出: `[qgw:gate2:S5-evolve] Dev-Rule 进化检查 ...` / `✅ 新增 N 条规则` 或 `✅ 无新增`

**引擎交互**：作为 S5 的子步骤执行，不独立注册到 gate-enforcer 状态机。

**触发条件**（满足任一即执行）：
- S4 verifier 有 FAIL（CODE 根因）
- S4 横切检查有 FAIL（CC-1~CC-6）
- Debug 模式修复了 BUG
- error-patterns frequency ≥ `evolve_threshold.error_pattern_frequency`
- P2.5 架构师 ISSUE 被接受（从 Gate 1 传递）

**执行流程**：

1. 读取 `.qgw/config.json` 的 `dev_rule` 配置
2. 如 `dev_rule.auto_evolve == false`，跳过并输出 `[qgw:gate2:S5-evolve] ⏭️ 已禁用`
3. 读取 `dev_rule.path`/SKILL.md
4. 从本次 Gate 2 产出中提取新规则（按 evolution-protocol.md §2.2 触发条件表）：
   - 反模式教训：S4 FAIL 的代码偏差模式 + 横切检查 FAIL + Debug BUG 根因
   - 核心规则：架构师根因簇升级 + error-patterns 阈值升级
5. 检查 AP 出现次数，达阈值执行升级（evolution-protocol.md §3）
6. grep 已有规则标题（`### CR-` 和 `### AP-`），避免重复
7. 追加到 SKILL.md 对应章节
8. 在进化日志追加一行记录
9. 更新 frontmatter `evolution_count += 1`
10. 如参考资源中有相关 pattern，在规则中引用（如 `参见 -dev-rule/backend-5.0-pattern`）
11. 输出：`[qgw:gate2:S5-evolve] ✅ 新增 AP-{N}、升级 CR-{M}`

**无进化时**：
输出 `[qgw:gate2:S5-evolve] ✅ 本次无新增规则`
仍递增 `evolution_count`（记录检查次数）。

**规则格式**：见 `shared/project-dev-rule-template/references/evolution-protocol.md` §1。

---

## Audit 模式

审查已有代码是否合规。报告模板见 `assets/report-templates.md`。

**A. 分解**

> 输出: `[qgw:audit:A] 分解 → N 个可审计 unit`

将 plan 分解为可审计 unit（一个页面/组件/API/方法 = 一个 unit）。

**B. 逐 unit 提取标准 + 自验**

执行 Step 1→3（跳过实现）。

**C. 并行派 verifier 子代理**

> 输出: `[qgw:audit:C] 并行派 N 个 verifier 子代理 ...`

每个 unit 一个 verifier，可并行。

**D. 汇总报告**

> 输出: `[qgw:audit:D] 汇总: N PASS, M FAIL (K 项偏差)`

```
## Audit Report: [Plan名称]
Date: [日期]
| Unit | Verifier结论 | 偏差 |
|------|-------------|------|
| Unit 1 | PASS | — |
| Unit 2 | FAIL | 3项: [列表] |
```

**E. 收敛修复**（用户要求时）

1. Round 1：修所有问题 → 新 verifier 再验
2. 仍有问题 → 报告用户 → 用户决定是否 Round 2
3. 硬顶 2 轮修复 + 2 次再验证
4. 每轮必须减少问题数（M < N），否则收敛失败 → 停止
5. **Audit 后重写计划时，新计划必须过 Gate 1 (P3→P5)**

**Fixer ≠ Verifier**：修复者和验证者必须是不同子代理。

---

## Debug 模式

无 Plan 的 bug 修复。

**D1. 定义修复标准**

> 输出: `[qgw:debug:D1] 定义修复标准 — Bug: [描述]`

**引擎交互**: `python gate-enforcer.py enter D1` → ... → `python gate-enforcer.py complete D1`

```
## Fix Criteria: [Bug描述]
症状: [确切行为或错误]
预期: [修好后的可测试结果]
回归边界: [不能变的相关功能、已有测试]
```

标准要求：症状写确切行为（如"显示 X 而非 Y"），预期写可测试结果，回归边界列具体范围。禁止"字段不对"、"修好"、"不影响其他"等模糊表述。

**D2. 最小修复**

> 输出: `[qgw:debug:D2] 最小修复 ...`

**引擎交互**: `python gate-enforcer.py enter D2` → ... → `python gate-enforcer.py complete D2`

禁止"顺便"重构。

**D3. 自验**

> 输出: `[qgw:debug:D3] 自验 ...` / `✅ 症状消除 + 预期达成 + 回归边界完整`

**引擎交互**: `python gate-enforcer.py enter D3` → ... → `python gate-enforcer.py complete D3`

验证：症状消除 + 预期达成 + 回归边界完整。

**D4. verifier 子代理 → 提交**

> 输出: `[qgw:debug:D4] verifier 验证` / `✅ 修复正确, 无回归 → 提交`

**引擎交互**: `python gate-enforcer.py enter D4` → ... → `python gate-enforcer.py complete D4 --toolCallId "Agent|D4|ISO-timestamp"` → **引擎强制检查 toolCallId**

verifier 检查修复正确性 + 无回归 + 无 over-fixing。同 S4，必须通过 `Task` 或 `Agent` 工具派发。

---

## Compaction Recovery

Context compaction 后，验收标准和进度会丢失。**必须从文件重建状态，禁止凭记忆或摘要继续。**

### 恢复流程

```
compact 发生 → 检测到 QGW 会话恢复
    ↓
1. 读取 Plan 文档末尾的验收清单（Acceptance Criteria Checklist）
2. 读取 docs/verification/unit-*.json（已完成的 Unit 验收数据）
3. 从验收清单 JSON 读取 feedbackRounds 和 evolveStatus，恢复上下文
4. 对比：哪些 Unit 已通过 S5，哪些未完成
5. 未完成的 Unit → 从其验收标准重新开始 S1
6. 禁止从摘要/记忆中"提取新标准"
```

### 关键规则

- ✅ 重读 Plan 文档验收清单
- ✅ 从 `docs/verification/unit-*.json` 恢复已完成状态
- ❌ 从上下文摘要中提取"剩余工作"（摘要会遗漏细节）
- ❌ 跳过 S1 直接从"上次停的地方"继续
- ❌ 不重读验收清单就实现

---

## 全链路复盘

用户使用 `--all` 或手动要求全链路审查时：

1. Gate 1 Audit：审查 Plan 完整性 vs PRD → Plan 偏差报告
2. Plan 通过 → 提示"是否继续审查 Code？"
3. 用户确认 → Gate 2 Audit：审查 Code vs Plan + PRD
4. 产出：Plan 偏差报告 + Code 偏差报告 + 可选修复

先修 Plan 再查 Code，避免反馈循环。
