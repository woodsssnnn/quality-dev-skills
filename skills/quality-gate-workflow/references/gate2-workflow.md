# Gate 2 工作流详细步骤

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
| `{message}` | 消息内容 | `实现Unit完成: 12项可验证项` |

**平台标识**：

| 平台 | 标识 | 会话存储位置 |
|------|------|--------------|
| MiMoCode | `mimo` | `~/.local/share/mimocode/memory/sessions/` |
| Claude Code | `claude` | `~/.claude/projects/{project-slug}/` |
| Codex | `codex` | `~/.codex/sessions/{year}/` |
| OpenCode | `opencode` | `~/.opencode/sessions/` |

**状态图标**：
- ✅ 步骤完成
- ❌ 步骤失败
- ⚠️ 警告/发现ISSUE
- 🔄 步骤进行中
- → 步骤开始/转移

**示例**：
```bash
[qgw][2026-06-17T20:45:00][mimo:ses_12ca2c1c4ffe0S3HguaG7fosHN][gate2][S0/5] → 工作空间检查
[qgw][2026-06-17T20:45:05][mimo:ses_12ca2c1c4ffe0S3HguaG7fosHN][gate2][S1/5] ✅ 提取验收标准完成: 12条标准
[qgw][2026-06-17T20:45:30][mimo:ses_12ca2c1c4ffe0S3HguaG7fosHN][gate2][STATS] 📊 总耗时: 30s | 步骤: 5/5 | 通过率: 100%
```

**复盘路径**：
```bash
# MiMoCode会话
cat ~/.local/share/mimocode/memory/sessions/{session_id}/checkpoint.md

# Claude Code会话
cat ~/.claude/projects/{project-slug}/conversations/{session-id}.json

# Codex会话
cat ~/.codex/sessions/2026/{session-id}/history.json
```

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

按验收标准写代码。

**读取 Scope**：实现前从 Plan 中读取当前 unit 的 Scope 声明（`allowedChanges` / `forbiddenChanges` / `estimatedLines`）。实现过程中只修改 allowed 路径内的文件，禁止修改 forbidden 路径内的文件。

**Dev-rule 代码骨架**（项目声明了 `dev_rule_path` 或 `gate_dev_rules` 且 Plan 指定了 pattern 时）：

1. 读取 Plan 中标注的 pattern 文件（如 `references/backend/patterns/backend-5.0-pattern/crud-api.md`）
2. 以 pattern 中的代码骨架为模板实现，保持架构一致
3. 同时读取 dev-rule 的 rules（如 Track-5.0 rules-5.0/ 或前端 rules/），遵循编码规范

未声明 `dev_rule_path`/`gate_dev_rules` 或 Plan 未指定 pattern 时，按常规实现。

---

## Step 2.5：Boundary Check

> 输出: `[qgw:gate2:S2.5] Boundary Check ...` / `✅ 所有变更在允许范围内` 或 `❌ N 处越界变更`

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

逐条检查每条标准：

- **Pass**：引用标准 + 引用代码 + 确认匹配
- **Fail**：引用标准 + 引用代码 + 说明偏差

修复所有 Fail 后进入 Step 3.5。

---

## Step 3.5：数据库 Schema 验证（后端专属）

> 输出: `[qgw:gate2:S3.5] Schema 验证 ...` / `✅ N 处 SQL 列名已确认` 或 `❌ M 处列不存在 → 修复中` 或 `⚠️ DB MCP 不可用, 跳过`

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

自验 100% 通过后，派子代理。详细 prompt 模板见 `references/verifier-templates.md`。

**硬性要求：必须通过 `Task` 或 `Agent` 工具调用派发子代理。禁止仅输出日志文本而不实际派发。**

没有实际的 Task/Agent 工具调用 = S4 未执行 = 禁止进入 S5。

子代理 prompt 必须包含：

1. 验收标准（Step 1 提取的）
2. 源需求文档位置
3. 实现代码位置
4. 指令：逐项报告 PASS/FAIL + 证据 + **Code Refs**（PASS 项的 file:lines + description，用于写入 verification JSON 的 codeRefs 字段）
5. Dev rule 合规检查（如果 CLAUDE.md 声明了 `dev_rule_path` 或 `gate_dev_rules`）
6. **数据库 Schema 抽检**（后端代码时）：verifier 从代码中随机抽取 2-3 处列名引用，通过 DB MCP 执行 `SHOW COLUMNS` 验证列存在。每处报告 PASS/FAIL + 表名 + 列名。不可用时跳过，报告 SKIP。

**Dev rule 前检**：派 verifier 前确认声明的每个 dev-rule 技能文件存在（`~/.agents/skills/{name}/SKILL.md` 或 `~/.claude/skills/{name}/SKILL.md` 或 `.claude/skills/{name}/SKILL.md`）。不存在 → 输出 `[qgw:gate2:S4] ⚠️ {name} 不存在，降级为仅检查验收标准`。禁止静默跳过。

**派发自检**：S4 完成后、进入 S5 前，确认本步骤确实产生了 `Task` 或 `Agent` 工具调用。工具调用失败 → 输出 `[qgw:gate2:S4] ❌ 子代理派发失败` 并报告用户，禁止静默跳过。

**物证链写入**：verifier 验证后（无论 PASS 或 FAIL），将本次工具调用记录写入验收清单 JSON：

1. 在 `verifierReports` 追加记录（含 `round`、`timestamp`、`result`、`toolCallId`），在 `toolCalls` 数组追加记录
2. `toolCallId` 格式：`"Agent|round{N}|{ISO-timestamp}"`（如 `"Agent|round2|2026-06-10T21:15:00"`）。禁止纯描述占位符（如 `"verifier"`、`"round1"`）。**禁止使用 `"main|"` 前缀**——S4 的 Writer≠Verifier 原则要求必须是独立子代理派发，主代理自验不算 S4 执行
3. `result` 为 FAIL 时，`failItems` 必须列出具体失败项 ID，禁止空数组
4. 在每个 PASS item 下设 `toolCallId` 为本次 toolCallId 值，并写入 `codeRefs`（从 verifier 输出的 Code Refs 提取）
5. 输出 `[qgw:gate2:S4] ✅ 物证链已写入: {toolCallId}`
6. **FAIL 或 PARTIAL 后触发 evolve**：首次 FAIL/PARTIAL 后立即创建 `docs/verification/error-patterns.json`，记录根因分类（CODE/PLAN）。不等 Unit 完成
7. **BUG 记录**：每轮 S4 修复（CODE 或 PLAN 根因）都应记录 BUG ID + 类型 + 根因 + 修复描述，供 Session Summary 的 Bug Log 章节使用（反模式 #34）
8. **无 toolCallId → 禁止进入 S5**

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

**S4 前置检查**：进入 S5 前，必须通过以下检查：

### 检查1: 物证链完整性
- 存在空 `toolCallId` → `[qgw] ❌ 存在未经验证的 item (toolCallId 为空) — 返回 S4 补验`
- 无工具调用记录 → `[qgw] ❌ 物证链缺失 — S4 未通过 Task/Agent 工具实际执行`
- PASS 项无 `codeRefs` → `[qgw] ❌ 可追溯性断裂 — 返回 S4 补充 codeRefs`（反模式 #30）

### 检查2: Plan文档同步
- Plan文档未更新 → `[qgw] ❌ Plan文档未同步 — 必须更新Task状态和实现记录`
- 验证项状态不一致 → `[qgw] ❌ Plan与verification不同步 — 必须对齐`

### 检查3: 5问题重启测试
- 无法回答"我在哪" → `[qgw] ⚠️ 会话状态不完整，需要重新加载`
- 无法回答"目标是什么" → `[qgw] ⚠️ 目标丢失，需要重新确认`

### 检查4: 错误记录完整性
- 存在未记录的错误 → `[qgw] ❌ 错误未记录到Plan文档 — 必须补充错误日志`
- 3次尝试未升级 → `[qgw] ⚠️ 违反3-Strike协议 — 必须报告用户`

**上述任一条件不满足 → 禁止提交**

**提交顺序**：先验证再提交。验证不通过禁止提交。禁止在 verifier 未实际执行（无工具调用）的情况下提交。

**验证结果写入结构化 JSON**（`references/acceptance-criteria-schema.json` 格式）。每个 Unit 通过 S5 后**必须**使用 `Write` 工具写入 `docs/verification/unit-{N}.json`。compaction 后可从文件恢复。

**提交后写入 commitSha**：git commit 后，读取最新 commit SHA，写入每个 PASS item 的 `commitSha` 字段。

**Git Trailer 生成**（反模式 #40）：

提交时在 commit message 末尾追加 QGW trailer（空行后 + trailer 行）：

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

```
## Fix Criteria: [Bug描述]
症状: [确切行为或错误]
预期: [修好后的可测试结果]
回归边界: [不能变的相关功能、已有测试]
```

标准要求：症状写确切行为（如"显示 X 而非 Y"），预期写可测试结果，回归边界列具体范围。禁止"字段不对"、"修好"、"不影响其他"等模糊表述。

**D2. 最小修复**

> 输出: `[qgw:debug:D2] 最小修复 ...`

禁止"顺便"重构。

**D3. 自验**

> 输出: `[qgw:debug:D3] 自验 ...` / `✅ 症状消除 + 预期达成 + 回归边界完整`

验证：症状消除 + 预期达成 + 回归边界完整。

**D4. verifier 子代理 → 提交**

> 输出: `[qgw:debug:D4] verifier 验证` / `✅ 修复正确, 无回归 → 提交`

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
