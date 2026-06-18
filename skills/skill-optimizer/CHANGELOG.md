# Changelog

All notable changes to skill-optimizer will be documented in this file.

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
