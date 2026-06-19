---
name: quality-gate-workflow
category: quality-assurance
description: |-
  Use when user requests quality-gated development workflow for requirements-to-code traceability,
  or when implementing features that need full traceability from PRD to code.
  Triggers on explicit parameters: --gate1, --gate2, --all, --self, --analyze, --auto, --preset.
  Also supports zero-parameter smart inference: describe your need and QGW suggests the right workflow.
allowed-tools:
  - Task
  - Agent
  - Read
  - Grep
  - Glob
  - Bash(git diff *)
  - Bash(git status *)
  - Bash(git log *)
triggers:
  parameters:
    - --gate1
    - --gate2
    - --all
    - --self
    - --analyze
  keywords:
    - 质量门禁
    - gate
    - plan
    - verifier
    - 验收
metadata:
  version: 0.8.0.1
integration:
  extends: []
  extended_by:
    - skill-optimizer
  shares_artifacts_with:
    - skill-optimizer
---

# 质量门禁工作流

> 需求不丢失、代码不偏离。两个 Gate 确保从 PRD 到 Code 的全链路质量保障。

- **Gate 1**：需求 → 验证过的 Plan + 验收清单
- **Gate 2**：Plan + 验收清单 → 验证过的 Code

---

## 快速开始（30 秒上手）

**方式 A — 零参数（推荐新手）**：直接描述你的需求，QGW 自动推断最佳流程并请你确认。

```
"帮我规划这个需求：用户注册需要邮箱验证..."     → 自动建议 --gate1 --prd
"这里有个 Bug：登录时偶发 500 错误..."           → 自动建议 --gate2 --debug
"按 docs/plan/user-auth.md 实现代码"              → 自动建议 --gate2 --impl
"重构支付模块，统一错误处理"                      → 自动建议 --gate1 --opt
```

> 智能推断规则详见 [references/first-run-guide.md](references/first-run-guide.md)。推断结果**必须用户确认后**才执行。

**方式 B — 场景预设**：

```
--preset quickfix    # 快速修 Bug（= --gate2 --debug）
--preset feature     # 完整功能开发（= --all --strict）
--preset hotfix      # 紧急修复全链路（= --gate1 --bug → --gate2 --debug）
--preset review      # 复盘最近会话（= --self）
--preset audit       # 审计已有代码（= --gate2 --audit）
--preset minimal     # 轻量快速通道（= --gate1 --lite → --gate2 --incremental）
```

> Preset 只是参数别名，展开后仍走完整 Gate 流程，**不绕过任何门禁**。

**方式 C — 显式参数（推荐进阶用户）**：`--gate1` / `--gate2` / `--all` / `--self` / `--analyze`

**安装**：`bash scripts/install.sh`（首次使用参见 `BOOTSTRAP.md`）| **详细安装** → [references/installation.md](references/installation.md)

---

## 智能推断规则（`--auto` 模式）

零参数时自动推断最佳流程。推断结果**必须用户确认后**才执行。

详细规则 → [references/smart-inference.md](references/smart-inference.md)

---

## 常用参数

### 一级参数：流程（必选其一）

| 参数 | 含义 |
|------|------|
| `--gate1` | Gate 1: 需求→Plan |
| `--gate2` | Gate 2: Plan→代码 |
| `--all` | 全流程 Gate 1+2 串行 |
| `--self` | 自检：复盘指定会话的 Gate 执行质量 |
| `--analyze` | 跨 artifact 一致性分析（只读） |

### 常用修饰符

| 参数 | 含义 | 适用 |
|------|------|------|
| `--strict` | 零偏差通过，否则阻断 | 任意 |
| `--lite` | 轻量快速通道（跳过 P1.5/P1.6/P1.7） | gate1, all |
| `--incremental` | 增量验证（只验证变更影响的 item） | gate2, all |
| `--e2e` | E2E 行为验证（运行项目测试套件） | gate2, all |
| `--prd-changed` | 声明 PRD 有变更（影响级别: cosmetic/minor/major） | gate2 |
| `--plan-tweak` | Gate 2 执行中对 Plan 做轻量微调（不改可验证项） | gate2 |

> 完整参数表（含二级模式、`--self` 子参数等）→ [references/full-parameters.md](references/full-parameters.md)

## 核心机制

- **五层防线**：提取验收标准 → **PM 顾问评议** → 写 plan → **架构师顾问评议** → 自验 → 独立 verifier 子代理
- **角色分工**：顾问判断"合不合理"（架构/业务），verifier 判断"对不对齐"（一致性）。两者不可互替
- **根因分类**：CODE（代码偏差，Gate 2 内修 ≤2 轮） / PLAN（计划偏差，反馈 Gate 1 硬顶 1 轮）
- **100% 通过才放行**，任何 FAIL 必须修复后重新验证

### 确定性执行引擎

Gate 工作流使用 `gate-enforcer.py` 确定性执行引擎管理步骤顺序和前置检查。

**规则**：每个步骤开始前必须调用 `python gate-enforcer.py enter <step>`，收到 `ALLOW` 后才可执行。收到 `BLOCK` 时必须修复问题后重试。每个步骤完成后必须调用 `python gate-enforcer.py complete <step>`。

引擎不替代语义判断——verifier 的 COVERED/MISSING、顾问的 ISSUE 评估仍由 LLM 完成。引擎只强制：步骤顺序、产出物存在性、格式合规性、skip 条件合法性。

```
# 初始化
python gate-enforcer.py init --gate gate1 --mode prd [--lite] [--strict]

# 每步骤交互
python gate-enforcer.py enter P0         # → ALLOW / BLOCK
[执行 P0 语义工作...]
python gate-enforcer.py complete P0      # → OK, next_step=P1
```

引擎状态文件：`docs/.qgw-engine-state.json`（可被 `--self` 和 `health-check.sh` 读取）。

### Gate 1 步骤

P1 → P1.5(DB) → P1.6(代码链路) → P1.7(PM 顾问) → P2 → P2.5(架构师顾问) → P3 → P4(verifier) → P5

`--lite` 跳过 P1.5/P1.6/P1.7。`--bug`/`--opt` 可跳过 P1.7。

### 顾问 vs verifier 边界

| 角色 | 身份 | 何时 | 关心 | 输出 | 派发方式 |
|------|------|------|------|------|---------|
| PM 顾问 | 独立 AI Agent | P1.7 | 需求合理性 | ISSUE + 隐含需求 + 严重性 | Task/Agent 工具调用 |
| 架构师顾问 | 独立 AI Agent | P2.5 | plan 架构合理性 | ISSUE + 根因簇 + 修复策略 | Task/Agent 工具调用 |
| verifier | 独立 AI Agent | P4 / S4 | plan ↔ PRD / code ↔ plan 一致性 | COVERED/PARTIAL/MISSING | Task/Agent 工具调用 |

所有三个角色都是独立 AI Agent，通过 Task/Agent 工具派发，不可由主代理自演。
**仅跑 verifier = 漏判架构/业务层问题**。仅跑顾问 = 漏判覆盖度问题。

## 合理化借口表（反驳清单）

主代理可能跳过顾问评议的常见借口，每条已预先反驳：

| 主代理借口 | 反驳 |
|-----------|------|
| "需求很简单，顾问浪费 token" | 07 任务 plan v2.0 标 90 项 PASS，5 类 PM/架构层问题全漏检。简单 ≠ 不会漏 |
| "PM 顾问是产品专家，我是开发做不了" | PM 顾问是子代理角色，主代理扮演即可（环境无 subagent 时）。prompt 模板见 `advisor-templates.md` |
| "架构我自己判断就行" | 主代理有沉没成本（自己写的 plan），架构师顾问无沉没成本，判断更客观 |
| "顾问 ISSUE 我主观认为不重要" | 必须给出技术理由，由 P4 verifier 复核驳回合理性 |
| "顾问跳过等下次再补" | 跳过必须有显式理由 + 日志，禁止静默跳过（anti-pattern #25）|
| "环境无 Agent 工具，跳过吧" | 主代理可显式扮演顾问角色 + 物证链记录角色边界，不等同于跳过 |
| "顾问和 verifier 重复了" | 顾问问"合不合理"，verifier 问"对不对齐"，覆盖不同维度 |
| "这是 bug 修复，跳过顾问" | `--bug` 仅可跳过 PM 顾问的 D2/D4/D5；架构师顾问 A3（局部 vs 全局）仍必做 |
| "gate-enforcer 调用浪费 token" | 引擎每次调用输出 ~50 token，远低于跳步导致的返工成本。确定性 > 概率 |

## 全部参数

完整参数表、参数组合矩阵和互斥规则 → [references/full-parameters.md](references/full-parameters.md)

## 进度输出

所有步骤必须使用 `[qgw]` 结构化日志格式。详细格式、平台标识、状态图标 → [references/progress-format.md](references/progress-format.md)

## 红线 - 停下来重新开始

**违反规则的字面意思就是违反规则的精神。**

- 跳过 verifier 验证（#1/#2）
- 静默跳过顾问评议（#25）
- 验收标准模糊（#5）— "有筛选功能" ❌，"筛选器=流程树多选 (§6.1.1)" ✅
- 需求猜测（#6）— 不问用户就解读需求
- 凭记忆提取标准（#8）— 不读文件就写 plan
- over-fixing（#20）— 修改超出回归边界
- 顾问自演（#27）— 主代理扮演顾问角色
- gate-enforcer 返回 BLOCK 时继续执行（#58）— 引擎前置检查是确定性的，BLOCK 意味着前置条件未满足

**以上任何一条都意味着：返回上一步，重新执行。禁止继续。**

## 常见错误与禁止行为

完整 60 条规则见 [references/anti-patterns.md](references/anti-patterns.md)。最常违规的：跳过 verifier（#1/#2）、验收标准模糊（#5）、需求猜测（#6）、凭记忆提取（#8）、over-fixing（#20）、顾问静默跳过（#25）、`--lite` 滥用（#26）、顾问自演（#27）。PRD 无版本化修订（#49）、文档变更无下游传播（#54）、PRD 非目录格式（#57）、绕过 gate-enforcer（#58）、PRD 变更不声明影响级别（#59）、Plan 微调修改可验证项（#60）。

## Knowledge Compounding（自进化）

每个 Unit 完成后执行 evolve 检查。详细机制 → [references/knowledge-compounding.md](references/knowledge-compounding.md)

## 项目配置

`.qgw/` 项目本地覆盖目录 + CLAUDE.md 兼容配置。详见 [references/project-config.md](references/project-config.md)。

## 安装

详见 [references/installation.md](references/installation.md)。

## 功能概览

功能概览详见 [references/feature-overviews.md](references/feature-overviews.md)。

## 错误输出格式

检测到反模式时使用人类可读格式输出。详细格式和示例 → [references/error-output-format.md](references/error-output-format.md)

## 路由分发

根据参数加载对应的 reference 文件（必须加载）：

| 参数/场景 | 加载文件 | 时机 |
|----------|---------|------|
| 零参数推断 | `references/smart-inference.md` | 推断前 |
| `--gate1` | `references/gate1-workflow.md` | P0 开始前 |
| `--gate2` | `references/gate2-workflow.md` | S0 开始前 |
| `--self` | `references/self-check-workflow.md` | SC0 开始前 |
| `--analyze` | `references/analyze-workflow.md` | AC0 开始前 |
| 查看完整参数 | `references/full-parameters.md` | 用户请求时 |
| 首次输出日志 | `references/progress-format.md` | 日志前 |
| 检测到反模式 | `references/error-output-format.md` | 检测时 |
| PRD 变更 | `references/prd-revision-workflow.md` + `references/plan-tweak-workflow.md` | `--prd-changed` 时 |
| Plan 微调 | `references/plan-tweak-workflow.md` | `--plan-tweak` 时 |
| Unit 完成后 | `references/knowledge-compounding.md` | evolve 检查时 |

## 参考文件索引

| 文件 | 内容 |
|------|------|
| [references/gate1-workflow.md](references/gate1-workflow.md) | Gate 1 P1→P5 详细步骤、Bug/Optimization 模式、反馈回路 |
| [references/gate2-workflow.md](references/gate2-workflow.md) | Gate 2 S0→S5、Schema 验证、Audit/Debug 模式、Compaction Recovery |
| [references/self-check-workflow.md](references/self-check-workflow.md) | Self-Check SC0→SC5、会话定位、日志提取、Plan 质量分析、报告生成 |
| [references/analyze-workflow.md](references/analyze-workflow.md) | Cross-Artifact 一致性分析 AC0→AC5 |
| [references/anti-patterns.md](references/anti-patterns.md) | 禁止行为完整规则（60 条去重） |
| [references/first-run-guide.md](references/first-run-guide.md) | 首次使用引导 + 智能推断规则 |
| [references/project-config.md](references/project-config.md) | 项目配置 + Preset 预设 + `.qgw/` 覆盖 |
| [references/prd-structure.md](references/prd-structure.md) | PRD 目录结构规范 + 全内容解析规则（文字+图片+表格+附件） |
| [references/prd-revision-workflow.md](references/prd-revision-workflow.md) | PRD 修订工作流 RV1-RV5（提案→影响分析→人工审批→执行→下游同步） |
| [references/change-propagation.md](references/change-propagation.md) | 文档变更传播规则 CP-1~CP-5（PRD/Plan/Code/Report/ErrorPattern） |
| [references/verifier-templates.md](references/verifier-templates.md) | Verifier 子代理 prompt 模板 + CROSS-CUTTING 横切检查清单 |
| [references/advisor-templates.md](references/advisor-templates.md) | PM 顾问 + 架构师顾问 prompt 模板 |
| [references/acceptance-criteria-schema.json](references/acceptance-criteria-schema.json) | 验收清单 JSON Schema v1.2（含 codeRefs/commitSha/chapter/prdSection/prdAssets）|
| [references/error-patterns.json](references/error-patterns.json) | 全局错误模式种子数据 |
| [references/regression-test-cases.md](references/regression-test-cases.md) | 回归测试用例集 |
| [references/constitution-template.md](references/constitution-template.md) | Gate 1 constitution 模板 |
| [evaluations/](evaluations/) | Skill 效果评估框架 |
| [scripts/gate-enforcer.py](scripts/gate-enforcer.py) | 确定性执行引擎（步骤状态机 + Guard 检查） |
| [references/general-protocols.md](references/general-protocols.md) | 通用工作协议（5问题重启测试、2-Action Rule、3-Strike Protocol） |
| [references/smart-inference.md](references/smart-inference.md) | 智能推断规则 + 推断决策树 + Preset 预设展开 |
| [references/full-parameters.md](references/full-parameters.md) | 全部参数表 + 参数组合矩阵 + 互斥规则 |
| [references/progress-format.md](references/progress-format.md) | 进度输出格式 + 平台标识 + 状态图标 |
| [references/error-output-format.md](references/error-output-format.md) | 错误输出格式 + 示例 + 错误级别 |
| [references/knowledge-compounding.md](references/knowledge-compounding.md) | Knowledge Compounding 自进化机制 + 阈值升级规则 |
| [references/plan-tweak-workflow.md](references/plan-tweak-workflow.md) | Plan 微调工作流 TW1-TW4（声明→分析→执行→标记） |

## 版本记录

→ [CHANGELOG.md](CHANGELOG.md)
