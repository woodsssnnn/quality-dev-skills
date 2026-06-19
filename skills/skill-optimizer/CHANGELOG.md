# Changelog

All notable changes to skill-optimizer will be documented in this file.

## [0.8.0.1] - 2026-06-19

### Changed
- SKILL.md 补齐 `category` / `triggers` / `integration` frontmatter
- description 改为 “Use when…” 格式
- 版本号跟随项目升级至 0.8.0.1

---

## [0.8.0.0] - 2026-06-18

### Added
- 新增 `references/scoring-rules.md`：9 条评分规则独立文档，支持细粒度打分
- evaluate.py 大幅增强：新增 `--dry-run`、`--target-score` 参数，支持多技能批量评估
- 新增技能清单 manifest 集成：优化结果可写入 skill-manifest.json

### Changed
- 版本号跟随项目升级至 0.8.0.0（生态升级版本）

---

## [0.7.1.0] - 2026-06-18

### Changed
- Prompt 瘦身：优化 rollout 指令精简重复内容
- 版本号跟随项目升级至 0.7.1.0

---

## [0.7.0.0] - 2026-06-18

### Added
- 集成确定性执行引擎：优化循环由 gate-enforcer.py 状态机驱动
- 新增反模式规则：gate-enforcer BLOCK 时禁止绕过

### Changed
- evaluate.py 输出格式对齐引擎 JSON 协议
- 版本号跟随项目升级至 0.7.0.0

---

## [0.6.0.0] - 2026-06-18

### Changed
- 版本号跟随项目升级至 0.6.0.0（文档全生命周期管理系统发布）

---

## [0.5.0.0] - 2026-06-18

> **版本号说明**：从 v1.0.0 降级至 v0.5.0.0。采用 4 级版本号（Major.Minor.Patch.Iteration），
> Major=0 表示项目仍在活跃开发期，架构尚未冻结。

### Added
- 新增 `--optimize` 参数式触发（与 `--target` 等价）
- 关键词触发保留作为 fallback

### Added - 初始发布
- 9 条评分规则（基于 best-practices）
- 优化循环：rollout → score → bounded edit → gate
- evaluate.py 评估脚本
- 反模式文档
- 测试用例模板

### Changed
- 版本号方案变更：SemVer 3 级 → 4 级（Major.Minor.Patch.Iteration）
- 版本降级：1.0.0 → 0.5.0.0（明确传达活跃开发状态）

---

## [1.0.0] - 2026-06-18 *(已合并至 0.5.0.0)*

### Added
- 初始开源发布
- 9 条评分规则（基于 best-practices）
- 优化循环：rollout → score → bounded edit → gate
- evaluate.py 评估脚本
- 反模式文档
- 测试用例模板
