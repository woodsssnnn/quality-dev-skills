# docs/plans/ — 实现计划文档

本目录存放质量门禁 Gate 1 产出的实现计划文档。Plan 必须按 PRD 章节结构组织。

## 目录结构（章节式，强制）

```
docs/plans/{feature}/
├── 00-overview.md              # 总览（frontmatter 含 PRD 版本、章节列表）
├── 01-prd-summary.md           # PRD 摘要 + 章节索引映射
├── 02-architecture.md          # 架构设计
├── 03-shared-infra.md          # 共享基础设施：DB Schema、通用组件、API 约定
├── ch-{X.X}-{name}/            # 按 PRD 章节分组
│   ├── README.md               # 章节概述 + PRD §X.X 原文引用
│   ├── unit-{N}-impl.md        # 实现计划
│   └── unit-{N}-acceptance.md  # 本章验收清单
└── 99-acceptance-summary.md    # 全局验收汇总
```

### 00-overview.md Frontmatter

```yaml
---
prd-source: docs/prd/{feature}/      # PRD 目录路径
prd-version: v1.0.0.0
plan-version: v1.0.0.0
chapters:
  - id: ch-2.1
    name: user-registration
    prd-section: "§2.1"
    units: [1, 2, 3]
    status: planned               # planned | in-progress | verified | needs_review
---
```

### 03-shared-infra.md

跨章节共享的内容必须集中在此文件：
- Database Schema（新增表、修改表、被引用章节）
- Common Components（组件名、路径、使用章节）
- API Conventions（RESTful 约定、分页、错误码）

每个共享项必须声明 `Dependents`（依赖它的章节列表）。

### ch-{X.X}/README.md

章节 README 必须包含：
1. PRD §X.X 的关键原文引用（反模式 #55）
2. 章节目标和约束
3. 涉及的 PRD 资产（图片/表格）

## 强制迁移

发现旧格式（扁平 `.md` 文件）必须重构为章节式目录结构（反模式 #51）。

## 与 verification/ 的关系

每个 Unit 对应 `docs/verification/` 下的一个 JSON 文件，包含 `chapter`、`prdSection`、`prdAssets` 字段。
