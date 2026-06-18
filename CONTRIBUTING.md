# Contributing to Quality Dev Skills

感谢你对 quality-dev-skills 的关注！我们欢迎各种形式的贡献。

## 行为准则

参与本项目前，请阅读 [Code of Conduct](CODE_OF_CONDUCT.md)。

## 如何贡献

### 报告 Bug

使用 GitHub Issues 报告 bug，请包含：

- **问题描述**：清晰简洁地描述问题
- **复现步骤**：最小复现步骤
- **期望行为**：你期望发生什么
- **实际行为**：实际发生了什么
- **环境信息**：OS、AI Agent 平台及版本（Claude Code / Cursor / MiMoCode 等）

### 提出新功能

使用 GitHub Issues 提出功能建议，请说明：

- **使用场景**：什么场景下需要这个功能
- **建议方案**：你期望的实现方式
- **替代方案**：你考虑过的其他方案

### 提交代码

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 确保变更通过现有技能的评估标准（可运行 `skill-optimizer` 自检）
4. 提交：`git commit -m "feat: add your feature"`
5. 推送并创建 Pull Request

### 改进文档

文档改进（包括中文和英文）同样受欢迎。

## 开发规范

### 技能开发

- 新技能使用 `shared/skill-template/SKILL.md.template` 模板
- SKILL.md 保持中文，README 中文为主、英文为辅
- 遵循 `skill-optimizer` 的 9 条评分规则
- reference 文件放在技能目录的 `references/` 下

### 提交信息格式

```
<type>(<scope>): <subject>

<body>
```

类型：`feat` / `fix` / `docs` / `refactor` / `test` / `chore`

### 分支策略

- `main` — 稳定版本
- `feature/*` — 功能开发
- `fix/*` — Bug 修复

## Pull Request 规范

- 描述清楚变更内容和原因
- 关联相关 Issue
- 一个 PR 只做一件事
- 确保不与 main 分支冲突

## 发布流程

1. 更新 `version.json` 中的版本号
2. 更新 `CHANGELOG.md`
3. 创建 Git Tag：`git tag v1.2.0`

## 许可

贡献的代码将以 MIT License 发布。提交 PR 即表示你同意将贡献以 MIT License 授权。
