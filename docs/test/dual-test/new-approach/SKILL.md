---
name: project-dev-rule
description: "项目开发规范（自进化）。随 Gate 1/Gate 2 工作过程自动沉淀术语、规则和反模式教训。当在项目空间内编写、修改、审查代码时自动加载。"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
metadata:
  version: 1.0.0
  generated_at: "2026-06-19"
  project_name: "qgw-test-project"
  evolution_count: 2
  template_source: "quality-dev-skills/shared/project-dev-rule-template"
---

# 项目开发规范（自进化）

> 本文件是项目的**活规范**，通过 Gate 1/Gate 2 的实际开发过程持续生长。
> 初始状态为空骨架，每次 Gate 完成后自动沉淀术语、规则和反模式教训。

## 项目身份

> 项目整体约束见 CLAUDE.md / AGENTS.md，本文件聚焦需求开发层面的规则和教训。

- **项目名称**：qgw-test-project
- **技术栈**：后端 Java/Spring Boot/MyBatis/Liquibase，前端 React/antd/TypeScript
- **构建命令**：后端 `mvn compile`，前端 `npx tsc --noEmit`

## 核心规则

### CR-001: TODO 状态值必须使用枚举常量
- **来源**: session-001 / Gate 1 P5-evolve / PM ISSUE-2
- **日期**: 2026-06-19
- **规则**: status 字段值只允许 'pending' 和 'done'，后端必须定义 TodoStatus 枚举，禁止硬编码字符串
- **反例**: 代码中出现 `status = "pending"` 字符串字面量
- **验证方式**: grep 后端代码，确认 status 比较全部走枚举

### CR-002: 逻辑删除字段统一使用 is_deleted
- **来源**: session-001 / Gate 1 P5-evolve / ARCH ISSUE-1
- **日期**: 2026-06-19
- **规则**: 所有表的逻辑删除字段统一命名为 is_deleted（tinyint DEFAULT 0），禁止使用 deleted/del_flag 等变体
- **反例**: 新建表使用 `del_flag` 字段名
- **验证方式**: grep DDL changelog 确认字段命名一致

## 反模式教训

### AP-001: 前端筛选参数与后端接口不匹配
- **来源**: session-001 / Gate 2 S5-evolve / FAIL CODE-3
- **日期**: 2026-06-19
- **反模式**: 前端传 status=all 但后端 SQL 未处理 all 值，导致查询空结果
- **正确做法**: 后端 Service 层对 status=all 时不添加 WHERE 条件；前端与后端约定 all 值为空字符串
- **出现次数**: 1

### AP-002: 分页参数未设置默认值
- **来源**: session-001 / Gate 2 S5-evolve / FAIL CODE-5
- **日期**: 2026-06-19
- **反模式**: Controller 接收 page/size 参数但未设默认值，前端不传时报 NPE
- **正确做法**: Controller 层 `@RequestParam(defaultValue = "1") int page, @RequestParam(defaultValue = "20") int size`
- **出现次数**: 1

## 术语表

| 术语 | 英文 | 定义 | 来源 |
|------|------|------|------|
| 待办事项 | TODO Item | 用户创建的待完成任务，包含标题和可选描述 | PRD §1 / session-001 |
| 逻辑删除 | Soft Delete | 通过 is_deleted 标记删除，不从数据库物理移除 | PRD §2 / session-001 |
| 状态筛选 | Status Filter | 前端下拉组件，按 pending/done/all 过滤列表 | PRD §4 / session-001 |

## 参考资源

> 声明的上游技能引用列表。参考技能是只读输入，本文件是活输出。
> 优先级：本文件规则 > 参考技能 > 通用规范。

<!-- 本项目未声明参考技能 -->

## 进化日志

| 日期 | Session | 来源 | 变更摘要 | CR 数 | AP 数 | 术语数 |
|------|---------|------|---------|-------|-------|--------|
| 2026-06-19 | session-001 | Gate 1 P5-evolve | +CR-001(状态枚举), +CR-002(逻辑删除命名), +术语3条 | 2 | 0 | 3 |
| 2026-06-19 | session-001 | Gate 2 S5-evolve | +AP-001(筛选参数不匹配), +AP-002(分页默认值) | 0 | 2 | 0 |
