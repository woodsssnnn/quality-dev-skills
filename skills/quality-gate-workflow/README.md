# 质量门禁工作流 (Quality Gate Workflow)

需求开发全链路质量保障技能。两个 Gate 确保需求不丢失、代码不偏离。

## 快速上手

1. 将本目录放到 `~/.agents/skills/quality-gate-workflow/`
   - 如果 AI 工具不使用 `~/.agents/skills/`，请软链接到工具的全局技能目录
2. 首次使用时说 `初始化质量门禁`（自动创建 `docs/plans/`、`docs/verification/`、`docs/reports/`、`docs/sessions/`）
3. 安装 Hook（推荐）：`bash ~/.agents/skills/quality-gate-workflow/scripts/hook-install.sh`
4. 详细工作流 → [SKILL.md](SKILL.md)

## 参数调用

| 流程参数 | 模式参数 | 修饰参数 |
|---------|---------|---------|
| `--gate1` (需求→Plan) | `--prd`(默认) / `--bug` / `--opt` | `--strict` |
| `--gate2` (Plan→代码) | `--impl`(默认) / `--audit` / `--debug` | `--strict` / `--fix` |
| `--all` (全流程) | 上述均可 | `--strict` / `--fix` |
| `--self` (自检复盘) | — | `--strict` |

**示例**：`"实现SP1 --gate2"` / `"审计报表 --gate2 --audit --fix"` / `"全流程 --all --strict"`

## 核心机制

- **五层防线**：提取验收标准 → PM 顾问评议 → 写 plan → 架构师顾问评议 → 自验 → 独立 verifier
- **Writer ≠ Verifier**：实现者和验证者是不同子代理
- **根因分类**：CODE（代码偏差）vs PLAN（计划偏差）
- **收敛硬顶**：Gate 内 ≤2 轮，反馈回路 ≤1 轮
- **自进化**：每次使用后自动积累新错误模式
- **文档生命周期**：Master Index + Session Summary + Plan 版本化
- **可追溯性链路**：验收项 → codeRefs → commitSha
- **结构化澄清**：多选题模式需求澄清
- **Boundary Enforcement**：代码变更范围检查
- **增量验证**：只验证变更影响的 item
- **Git Trailer**：commit message 嵌入验证状态
- **Cross-Artifact 分析**：多方向一致性检查
- **Extensions/Presets**：`.qgw/` 项目本地覆盖机制
- **E2E 行为验证**：运行时测试验证

## 文件结构

```
quality-gate-workflow/
├── SKILL.md                              # 核心技能文件（必读）
├── README.md                             # 本文件（快速上手）
├── CHANGELOG.md                          # 版本记录
├── scripts/
│   ├── verify-checkpoint.sh              # 提交前验收检查（Hook, 7 项检查）
│   ├── hook-install.sh                   # Hook 安装（支持 --mode）
│   └── hook-uninstall.sh                 # Hook 卸载
├── references/
│   ├── gate1-workflow.md                 # Gate 1 P1→P5 详细步骤
│   ├── gate2-workflow.md                 # Gate 2 S1→S5 + Audit/Debug 详细步骤
│   ├── analyze-workflow.md               # Cross-Artifact 一致性分析 AC0→AC5
│   ├── anti-patterns.md                  # 禁止行为完整规则（46 条去重）
│   ├── acceptance-criteria-schema.json   # 验收清单 JSON Schema v1.2
│   ├── error-patterns.json               # 全局错误模式种子数据
│   ├── regression-test-cases.md          # 回归测试用例集
│   ├── verifier-templates.md             # Verifier 子代理 prompt 模板
│   ├── advisor-templates.md              # PM + 架构师顾问 prompt 模板
│   ├── constitution-template.md          # Gate 1 constitution 模板
├── evaluations/                          # Skill 效果评估框架
│   ├── README.md
│   ├── scenario-1-trigger-accuracy.md
│   ├── scenario-2-gate1-adherence.md
│   ├── scenario-3-gate2-adherence.md
│   ├── scenario-4-debug-mode.md
│   └── scenario-5-anti-patterns.md
└── assets/
    ├── report-templates.md
    └── workspace-readmes/
        ├── plans-README.md
        ├── verification-README.md
        └── reports-README.md
```

## 版本记录

→ [CHANGELOG.md](CHANGELOG.md)

