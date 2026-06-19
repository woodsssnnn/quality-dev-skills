---
name: project-dev-rule
description: "Use when the agent is writing, modifying, reviewing, or questioning any project code. Triggers on: [AI根据项目上下文填写]."
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
metadata:
  version: 1.0.0
  generated_at: "2026-06-19"
  template_version: "1.0.0"
  project_name: "qgw-test-project"
---

# 项目开发规范

## 快速开始

**做什么**：[AI根据项目上下文填写：一句话描述技能解决的问题]
**怎么触发**：[AI根据项目上下文填写：自动触发条件]
**前置条件**：[AI根据项目上下文填写：需要的环境或权限]
**第一次用**：[AI根据项目上下文填写：首次使用步骤]

## 核心原则

[AI根据项目上下文生成3-5条核心原则]

1. **[原则1]** — [具体说明]
2. **[原则2]** — [具体说明]
3. **[原则3]** — [具体说明]

## 后端规范

[AI根据项目技术栈生成后端规范]

### 分层规范

[生成Controller/Service/Repository等分层规范]

### 命名规范

[生成类名、方法名、变量名命名规范]

### 异常处理

[生成异常处理规范]

## 前端规范

[AI根据项目技术栈生成前端规范]

### 组件规范

[生成组件文件结构、命名、props设计规范]

### 状态管理

[生成状态管理规范]

### 样式规范

[生成样式规范]

## 业务规范

[AI根据项目业务生成业务规范]

### 术语表

[生成项目核心术语]

### 模块结构

[生成业务模块划分]

## 验证清单

[AI根据项目规范生成验证清单]

### 开发前检查

- [ ] 检查项1
- [ ] 检查项2

### 代码审查检查

- [ ] 检查项1
- [ ] 检查项2

## 红线规则

[AI根据项目规范生成红线规则，绝对禁止的行为]

### 绝对禁止

- [禁止行为1]
- [禁止行为2]

## 常见错误

[AI根据项目经验生成常见错误和解决方案]

## 参考

- [共享最佳实践](../shared/agent-skills-best-practices.md)
- [质量门禁工作流](../../quality-gate-workflow/SKILL.md)
