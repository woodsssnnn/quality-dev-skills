# Changelog

## 0.8.0.1 (2026-06-19)

- SKILL.md 补齐 `category` / `triggers` / `integration` frontmatter
- 版本号跟随项目升级至 0.8.0.1

---

## 0.8.0.0 (2026-06-18)

- 初始版本：交互式 7 步引导 + 非交互式 qgw-init.sh 脚本
- 支持 5 个平台适配器（claude-code / codex / opencode / mimo / general）
- 3 种工作流模式（lite / full / ultra）
- 自动平台检测 + 用户确认
- `.qgw/` 配置目录生成（config.json + constitution.md）
- `docs/` 产出物目录创建（plans / verification / reports / sessions）
- 可选 PRD 目录结构创建
- 平台配置写入（settings.local.json / AGENTS.md / plugin.mjs / plugin.json）
- 健康检查验证集成（复用 quality-gate-workflow/scripts/health-check.sh）
- 完整参考文档：平台适配器配置 + 工作流模式差异说明
