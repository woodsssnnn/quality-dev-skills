# 功能概览

## 文档生命周期

QGW 确保所有文档有据可查：

### Master Index

`docs/QGW-INDEX.md` 是中央索引，每次 P0/S0/P5/S5 自动维护。包含：
- **Active Sessions**：所有 QGW session 的状态和关联文档
- **Document Registry**：Plan/Verification/Report 的版本和时间戳
- **Clarifications**：澄清文件与 Plan 的关联

### Session Summary

`docs/sessions/{session-id}.md` 在 P5/S5 完成后自动写入。包含：
- **Execution Flow**：每个步骤的 Status + Notes
- **Decisions**：跳过的步骤及理由、顾问 ISSUE 响应
- **Traceability**：验收项 → codeRefs → commitSha
- **Bug Log**：S4 中发现并修复的 BUG

### Plan 版本化

Plan 修改时追加 `QGW-VERSION` 行：

```markdown
<!-- QGW-VERSION: v1.1 | 2026-06-15T14:30:00Z | reason: feedback round 1 -->
```

## 可追溯性链路

验收项 → 代码变更 → git commit 的完整链路：

- **codeRefs**：每个 PASS 的验收项记录具体代码变更位置（file:lines + description）
- **commitSha**：提交后写入 git commit SHA
- **Session Summary Traceability 表**：汇总所有验收项的追溯信息

## 变更管理

### Plan BUG 修复

Gate 2 发现 PLAN 根因时：
1. 修改 Plan + 追加 `QGW-VERSION` 行
2. 重置受影响 item 的 status 为 PENDING
3. 更新 INDEX 版本号
4. 记录到 session summary Decisions 表

### PRD 更新检测

Gate 2 S0 检测 PRD 文件修改时间 vs Gate 1 完成时间：
- 有修改 → 标记受影响 item 为 NEEDS_REVIEW
- 询问用户：增量更新或继续

### BUG 记录

每轮 S4 修复都记录到 session summary `## Bug Log`：

```markdown
| BUG-001 | PLAN | S4 verifier | 筛选器写成单选 | PLAN 根因 | Plan v1.1 修正 |
```

## 结构化澄清

借鉴 Spec Kit 的 `/speckit.clarify`，将需求澄清从口头/自由模式升级为结构化多选题模式：

- **默认使用结构化澄清**：P1 发现歧义后自动生成 3-5 候选项的多选题
- **用户选字母回答**：减少思考负担，提高记录完整性
- **自由澄清兜底**：仅在歧义开放、无明确候选项时使用
- **记录完整**：选项 + 选择 + 理由 → 写入 `_clarifications.md`

## Boundary Enforcement

借鉴 agent-spec 的 boundary enforcement，在 Gate 2 新增 Step 2.5：

- **Plan 声明范围**：每个 plan unit 必须声明 `allowedChanges`（允许变更的文件路径模式）
- **自动检查**：S2 实现后用 `git diff --name-only` 对照 allowedChanges
- **越界拦截**：超出范围的变更必须回滚或更新 Plan 后重走 S2
- **防止 over-fixing**：机械式拦截，不是建议

## 增量验证

借鉴 OpenSpec 的 delta specs（只描述变更部分），增量验证只验证**受代码变更影响的验收项**：

- **触发**：`--gate2 --incremental` 或 `--all --incremental`
- **原理**：`git diff` → 映射 verification JSON 的 codeRefs → 只验证受影响 item
- **SKIPPED**：未受影响的 item 标记为 SKIPPED（不验证、不计入通过率）
- **前提**：必须有已有 verification JSON（至少一个 unit 已通过 S5）
- **Boundary 不受影响**：S2.5 boundary check 始终执行

## Git Trailer

借鉴 agent-spec 的 `stamp` 命令，每次 QGW 提交自动在 commit message 末尾追加验证状态 trailer：

```
QGW-Gate: gate2
QGW-Status: verified
QGW-Plan: docs/plans/feat-07-process-track.md
QGW-Session: ses-0616-01
QGW-Items: 12/12 PASS
QGW-Mode: full
```

- **反查**：`git log --grep="QGW-Status: verified"` 找到所有验证过的 commit
- **增量模式**：`QGW-Mode: incremental`，`QGW-Items: 3/12 PASS, 9 SKIPPED`
- **Gate 1 提交**：同样生成 trailer（`QGW-Gate: gate1, QGW-Status: planned`）

## Cross-Artifact 一致性分析

借鉴 Spec Kit `/speckit.analyze`，`--analyze` 对项目所有 artifact 做多方向交叉检查：

- **PRD → Plan**：每个 PRD §X.X 是否有对应 Plan unit
- **Plan → Verification**：每个 Plan unit 是否有对应 verification item
- **Verification → Code**：每个 PASS item 是否有 codeRefs + commitSha
- **Cross-Unit**：Unit 之间是否有未声明的依赖
- **Scope 完整性**：Plan 的 allowedChanges 是否覆盖所有 verification codeRefs

只读操作，不修改文件。详细步骤见 `references/analyze-workflow.md`。

## E2E 行为验证

借鉴 Autonoma 的 agentic testing，S4 验证"代码匹配 Plan"（静态），E2E 验证"代码正确运行"（动态）：

- **触发**：`--gate2 --e2e` 或 `--all --e2e`
- **流程**：S4 通过后 → S4.5 自动检测测试框架 → 执行测试 → 解析结果
- **支持框架**：jest/vitest（npm test）、Maven（mvn test）、pytest、Playwright
- **自定义命令**：`.qgw/config.json` 中 `e2e.command` 指定
- **E2E FAIL**：返回 S2 修复，收敛 ≤2 轮
- **E2E SKIP**（无测试）：警告但不阻止
