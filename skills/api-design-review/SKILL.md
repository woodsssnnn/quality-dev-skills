---
name: api-design-review
category: vertical
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
description: "Use when reviewing REST API design for convention compliance. Triggers on: --api-review, API review, REST convention."
triggers:
  parameters:
    - --api-review
  keywords:
    - API review
    - REST convention
    - endpoint design
    - OpenAPI
metadata:
  version: 0.8.0.0
integration:
  extends:
    - quality-gate-workflow
  extended_by: []
  shares_artifacts_with:
    - quality-gate-workflow
---

# API 设计审查

检查 REST API 设计是否符合团队约定的 API 设计规范，包括 URL 命名、HTTP 方法使用、响应码规范和 OpenAPI 一致性。

## 核心原则

1. **资源导向** — URL 表示资源，HTTP 方法表示操作
2. **一致性** — 同类资源的命名、响应结构保持一致
3. **规范兼容** — 与 OpenAPI 3.0 spec 保持一致

## 何时使用

- 新增或修改 API endpoint 时
- Code Review 中涉及 API 接口变更
- 发布前检查 OpenAPI spec 与实现一致性

## 快速参考

| 场景 | 做法 |
|------|------|
| 新增 endpoint | 运行 `python scripts/check-api-convention.py <spec-file>` |
| Review PR | 对变更的路由文件运行检查脚本 |
| 批量审查 | 对 OpenAPI spec YAML/JSON 运行全量检查 |

## 检查项

| # | 检查项 | 严重度 |
|---|--------|--------|
| 1 | URL 使用 kebab-case，复数名词 | ERROR |
| 2 | GET 无副作用，POST 用于创建 | ERROR |
| 3 | 正确使用 HTTP 状态码（200/201/204/400/404/500） | ERROR |
| 4 | 分页参数使用 `page` + `page_size` | WARN |
| 5 | 错误响应包含 `code` + `message` | WARN |
| 6 | OpenAPI spec 与实际路由一致 | ERROR |

## 参考

- [API 设计约定](references/api-conventions.md)
- [垂直技能开发指南](../../shared/vertical-skill-guide.md)
