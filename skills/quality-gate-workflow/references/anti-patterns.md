# Anti-Patterns（质量门禁禁止行为）

> 合并自 Red Lines + Common Mistakes + Rationalization Table，去重后唯一规则。

## 验证与提交

1. S4/P4 必须通过 Task/Agent 工具派发 verifier 子代理。无工具调用 = 未执行。将 toolCallId 写入验收 JSON，空 toolCallId 禁止进入下一步。
2. 自验通过后必须再经独立 verifier 验证。自我审查偏见是规格漂移的头号原因，对简单和复杂 unit 一视同仁。
3. 先验证再提交。验证不通过禁止 commit。
4. 逐 unit 走全流程（S1→S5），禁止批量实现后再统一验证。

## 需求与标准

5. 验收标准必须具体可验证（"筛选器=流程树多选"而非"有筛选器"），每项追溯到源 §X.X 或 §C[N]。
6. 需求有歧义时停下来问用户，禁止猜测或自行解读。
7. PRD 每个枚举项（角色/类型/选项）必须在方案中逐个说明处理方式，禁止用"默认/不处理"跳过。
8. 重读 Plan AND 源需求文档，禁止凭记忆提取标准。
9. 文字与原型图/图片不一致时必须澄清并记录到 `_clarifications.md`，禁止只取文字忽略图片。

## 持久化与恢复

10. 验收清单必须持久化到 Plan 文档和 `docs/verification/unit-*.json`（使用 `Write` 工具）。仅写入 Markdown 附录不算完成。P5/S5 结束后必须确认 JSON 文件存在，不存在 = 步骤未完成。context compaction 后禁止从摘要提取标准，必须重读文件恢复。
11. 口头澄清必须写入 `_clarifications.md`。不记录 = 丢失。

## 数据库（后端）

12. 后端需求必须在 Gate 1 执行 P1.5 数据库调查（表结构/枚举值域/数据样例），禁止凭记忆假设列名或表关系。
13. Gate 2 后端代码必须通过 Step 3.5 Schema 验证（DESCRIBE/SHOW COLUMNS 确认列存在），编译不拦字符串列名。
14. DB MCP 不可用时必须输出 ⚠️ 警告，列出受影响的具体验收项 + 替代验证手段，禁止静默跳过。
15. 过滤方法（getXxxClause）必须与目标表类型匹配，验证时对照表名-方法映射表。

## Gate 跳跃与全局写入

16. 只有用户能跳过 Gate 1。代理无权跳过。Audit 重写的计划是新产物，必须过 Gate 1 P3→P5。
17. 自动提取的错误模式只写工作空间层 `docs/verification/error-patterns.json`。全局层必须用户确认后 promote。**P4/S4 verifier 返回 FAIL 或 PARTIAL 后必须立即创建**（不等 Unit 完成），文件不存在不是跳过的理由。

## Dev-rule 与降级

18. Dev-rule 加载失败时必须显式警告并降级，禁止静默跳过。
19. evolve 检查每个 Unit 完成后必须执行，无 FAIL 也确认"无新增 pattern"，禁止跳过。

## Debug 修复

20. 修复标准必须具体（症状 + 预期 + 回归边界）。禁止 over-fixing，"顺便"改动超出回归边界的代码绕过了验证。
21. verifierReports 中 `result` 为 FAIL 时，`failItems` 必须列出具体失败项 ID（如 `["V2.3", "V2.4"]`）。空数组的 FAIL 记录 = 未正确记录，禁止写入。`toolCallId` 必须包含轮次和时间戳（如 `"Agent|round1|2026-06-10T21:15:00"`），禁止纯描述占位符（如 `"verifier"`、`"round1"`）。
22. P1.6 代码链路调查禁止跳过。grep 必须覆盖全部涉及层（5.0/4.0/3.0/前端）。"纯新增功能不需要调查"是错误判断——新增也需要匹配已有 pattern 和确认无冲突。调用点清单精确到文件+行号，"大致位置"不算完成。
23. P1 出口检查点（P1→P2 之间）禁止跳过。必须输出 `[qgw:gate1:P1-check]` 日志明确记录 P1.5 和 P1.6 的执行/跳过决策及理由。无此日志直接进入 P2 = 静默跳过，即使 P1.5/P1.6 实际不需要也必须显式声明。

## 横切检查

24. Gate 2 S4 verifier 必须执行 CROSS-CUTTING 横切检查（见 `verifier-templates.md` 的 CROSS-CUTTING 章节），覆盖 6 项：SQL/Java key casing / 工具方法参数顺序 / @PreAuthorize 覆盖率 / 异常 vs HTTP status / 邮件场景数量 / N+1 查询。横切报告作为 S4 独立章节输出，任一 FAIL → 整个 S4 FAIL。所有 6 项全部跳过 = 横切检查未执行（任何代码改动至少触发 1 项）。源自 07 流程穿透任务复审：90 项 unit PASS 但 4 个 P0 横切 BUG 全漏检。

## 顾问评议

25. Gate 1 P1.7（PM 顾问）和 P2.5（架构师顾问）禁止静默跳过。`--prd` / `--all` 模式 + 任何含业务逻辑的需求**必须**派 PM 顾问；任何涉及 SqlProvider/Mapper/DTO/共享组件的修改、≥2 unit 的 plan、含"修复策略选择"的 plan **必须**派架构师顾问。顾问 ISSUE 主代理必须逐条响应（接受/驳回+理由），禁止"主观认为不重要"模糊驳回。源自 07 流程穿透任务复审：90 项 unit PASS 但 PM 层（U8-5 邮件配置 PASS ≠ 实现 PASS、U1-10 PRD 笔误未澄清）+ 架构层（P0-1/2 修复策略、marks-number 技术债）共 5 类问题漏检。

## 轻量模式与顾问独立性

26. `--lite` 模式必须同时满足三个适用条件：单文件/单函数改动 + 无跨文件依赖 + 无架构决策。不满足任一条件则必须退回标准流程（P1.5/P1.6/P1.7 不可跳过）。禁止以"改动看起来简单"为由使用 `--lite` 跳过必要步骤。
27. PM 顾问和架构师顾问必须通过 Task/Agent 工具调用派发为独立 AI Agent，禁止主代理自演顾问角色。自演 = 未执行（同反模式 #1 对 verifier 的要求）。顾问的 toolCallId 必须使用 `"Agent|P1.7|..."` 或 `"Agent|P2.5|..."` 格式，禁止 `"main|"` 前缀。

## 文档生命周期与可观测性

28. 有 plan/verification 但 `docs/QGW-INDEX.md` 缺失。QGW 每次执行（P0/S0）必须创建或更新 INDEX，记录 session、document registry、clarifications。
29. QGW 完成（P5/S5）后未写入 session summary（`docs/sessions/{id}.md`）。session summary 是 `--self` 可观测性的基础，包含 Execution Flow、Decisions、Traceability、Bug Log。
30. Gate 2 S5 提交时 PASS 项无 `codeRefs`。可追溯性断裂 = 无法定位变更来源。verifier 必须输出 codeRefs，主代理写入 verification JSON。
31. 在非开发场景下应使用 `QGW_HOOK_MODE=off`（通过 settings.local.json 配置），而非 `--no-verify`。`--no-verify` 跳过所有 hook（含 git 自身检查），`QGW_HOOK_MODE=off` 仅跳过 QGW 检查。

## 变更管理

32. Plan BUG 修复（feedback 回路）时不追加 `QGW-VERSION` 行。版本标记是 compaction 恢复和 `--self` 复盘的基础。每次修改 Plan 必须追加 `<!-- QGW-VERSION: vX.X | timestamp | reason: ... -->`。
33. PRD 文件修改后不检查受影响的可验证项。Gate 2 S0 应检测 PRD 文件修改时间 vs Gate 1 完成时间，如有变更则标记受影响 item 为 NEEDS_REVIEW 并询问用户是否增量重跑 Gate 1。
34. BUG 修复不记录到 session summary Bug Log。每轮 S4 修复（CODE 或 PLAN 根因）都应记录 BUG ID + 类型 + 根因 + 修复描述到 `## Bug Log` 章节。新错误模式触发 evolve。

## 结构化澄清与边界检查

35. P1 发现歧义但不生成结构化澄清问题，直接自行解读。结构化澄清（多选题模式）是默认澄清方式，仅在歧义开放、无明确候选项时降级为自由澄清。自行解读 = 反模式 #6。
36. 代码变更超出 Plan 定义的 `allowedChanges` 范围且未更新 Plan。Boundary enforcement 是 Gate 2 S2.5 的机械式拦截，越界变更必须回滚或更新 Plan 后重走 S2。
37. Plan unit 未声明 `allowedChanges` / `forbiddenChanges`。每个 plan unit 在 P2 撰写时必须声明变更范围（文件路径模式），否则 S2.5 无法执行 boundary check。

## 增量验证

38. `--incremental` 用于首次 Gate 2（无已有 verification JSON）。增量验证必须有基线数据——至少一个 unit 已通过 S5，verification JSON 存在且含 codeRefs。
39. `--incremental` 跳过 S2.5 boundary check。Boundary check 始终执行，不受增量模式影响。越界变更在任何模式下都必须拦截。

## Git Trailer

40. S5/P5 提交时不生成 QGW trailer。每次 QGW 提交都必须在 commit message 末尾追加 `QGW-Gate` / `QGW-Status` / `QGW-Plan` / `QGW-Session` / `QGW-Items` trailer，作为 git 历史中可追溯的验证标记。

## Cross-Artifact 分析

41. 提交前不运行 `--analyze`。跨 artifact 一致性分析是提交前的轻量级自检，发现 MISSING/BROKEN/DEPENDENCY 后必须修复或显式标注 ACCEPTABLE，不替代 P4/S4 verifier。
42. `--analyze` 发现问题后不修复直接提交。分析报告中的每个问题都必须修复或在报告中标注 ACCEPTABLE + 理由。

## Extensions/Presets

43. 绕过 `.qgw/` 覆盖直接修改 skill 文件。项目定制必须通过 `.qgw/` 目录，禁止修改 `~/.agents/skills/quality-gate-workflow/` 下的文件。
44. `.qgw/anti-patterns.md` 格式与全局不一致。项目 anti-patterns 必须遵循全局格式（编号 + 规则描述），否则 agent 无法解析。

## E2E 行为验证

45. `--e2e` 跳过 S4 静态验证。E2E 是 S4 的补充而非替代——静态验证检查 Plan 对齐，E2E 检查运行时行为，两者都必须通过。
46. E2E 失败后不修复直接提交。E2E FAIL 必须修复后重新验证，与 S4 CODE 根因收敛规则一致（≤2 轮）。

## Plan 文档更新

47. Gate 2 完成后不更新 Plan 文档。Gate 2 Step 5 必须更新 Plan 文档中的 Task 状态、可验证项状态和 Gate 2 实现记录，实现全生命周期闭环。未更新 = 反模式 #47。
48. Plan 文档与 verification JSON 不同步。Plan 中的可验证项状态必须与 `docs/verification/unit-*.json` 保持一致。不同步 = 反模式 #48。
