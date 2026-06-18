# Changelog

All notable changes to quality-gate-workflow will be documented in this file.

## [1.0.0] - 2026-06-18

### Added
- 初始开源发布
- 质量门禁工作流：Gate 1（需求→Plan）+ Gate 2（Plan→代码）全链路验证
- 五层防线：验收标准提取 → PM 顾问评议 → Plan 撰写 → 架构师顾问评议 → 独立 verifier 验证
- 参数式触发：`--gate1` / `--gate2` / `--all` / `--self` / `--analyze`
- 模式支持：PRD / Bug / Optimization / Implementation / Audit / Debug
- 修饰参数：`--strict` / `--lite` / `--incremental` / `--e2e` / `--fix`
- 结构化需求澄清（多选题模式）
- Boundary Enforcement（变更范围检查）
- 增量验证（`--incremental`）
- Git Trailer 可追溯性
- Cross-Artifact 一致性分析（`--analyze`）
- E2E 行为验证（`--e2e`）
- CROSS-CUTTING 横切检查清单（6 项）
- 文档生命周期：Master Index + Session Summary + Plan 版本化
- Knowledge Compounding 自进化机制
- 结构化日志格式
- 多平台支持：Claude Code / Codex / OpenCode / MiMoCode / 通用
- 46 条反模式规则 + 合理化借口反驳清单
- 评估框架（5 个场景 + 5 个指标）
- 回归测试用例集（10 个 RC）
