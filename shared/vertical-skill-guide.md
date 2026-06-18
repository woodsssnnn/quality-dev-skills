# 垂直领域技能包开发指南

垂直技能包（vertical skill）是针对特定技术领域（如 API 设计、数据库迁移、安全审计）的质量门禁扩展。它们与核心 `quality-gate-workflow` 协同工作，在通用质量门禁之上叠加领域专属检查。

## 什么是垂直技能

| 类型 | 说明 | 示例 |
|------|------|------|
| 核心技能 | 通用质量门禁，适用所有项目 | quality-gate-workflow |
| 垂直技能 | 特定技术领域的专属检查 | api-design-review, db-migration-gate |
| 工具技能 | 辅助工具（优化、初始化） | skill-optimizer, qgw-init |

## 开发步骤

### 1. 确定技能边界

- **单一职责**：一个垂直技能只解决一个技术领域的问题
- **不重复核心**：不要复制 quality-gate-workflow 已有的检查
- **明确触发**：必须有专属参数触发（如 `--api-review`），避免与核心技能冲突

### 2. 创建目录结构

```bash
mkdir -p skills/your-skill/{references,scripts,evaluations}
```

完整结构：

```
skills/your-skill/
├── SKILL.md              ← 主入口（必需）
├── manifest-entry.json   ← 清单项（必需）
├── references/           ← 领域约定文档
│   └── conventions.md
├── scripts/              ← 自动检查脚本
│   └── check-*.py        ← stdlib only
└── evaluations/          ← 评估场景（≥3 个）
    ├── scenario-1-normal.md
    ├── scenario-2-edge.md
    └── scenario-3-error.md
```

### 3. 编写 SKILL.md

必须包含的 frontmatter 字段：

```yaml
---
name: your-skill
category: vertical
triggers:
  parameters:
    - --your-trigger
  keywords:
    - keyword1
description: "Use when ... Triggers on: --your-trigger."
metadata:
  version: 1.0.0
integration:
  extends:
    - quality-gate-workflow
  shares_artifacts_with:
    - quality-gate-workflow
---
```

### 4. 编写检查脚本

- **stdlib only**：只用 Python 标准库
- **输入约定**：通过命令行参数接收目标文件路径
- **输出约定**：exit code 0 = PASS, 1 = FAIL, 2 = WARN
- **输出格式**：每行一条，`[LEVEL] file:line: message`

### 5. 注册到 manifest

创建 `manifest-entry.json`：

```json
{
  "id": "your-skill",
  "category": "vertical",
  "triggers": {
    "parameters": ["--your-trigger"],
    "keywords": ["keyword1"]
  },
  "inputs": {
    "required": ["目标文件路径"],
    "optional": ["--strict"]
  },
  "outputs": {
    "artifacts": [],
    "side_effects": []
  },
  "integration_points": {
    "extends": ["quality-gate-workflow"],
    "extended_by": [],
    "shares_artifacts_with": ["quality-gate-workflow"]
  }
}
```

然后运行：

```bash
python scripts/generate-manifest.py
python scripts/generate-manifest.py --validate
```

## 与核心技能的集成模式

### 模式 A：前置检查（Pre-check）

垂直技能在 Gate 1 之前运行，产出作为 Gate 1 的输入：

```
垂直技能检查 → 检查报告 → Gate 1 P1 引用
```

### 模式 B：内嵌检查（Inline）

垂直技能作为 Gate 2 的附加步骤运行：

```
Gate 2 S1 → S2 → ... → S4 → 垂直技能检查 → 完成
```

### 模式 C：独立运行（Standalone）

垂直技能独立触发，不依赖核心流程：

```
--your-trigger → 垂直技能 → 检查报告
```

## 质量要求

- evaluate.py 评分 >= B 级
- 3 个以上评估场景
- 所有脚本通过 py_compile
- ShellCheck 通过（.sh 文件）
- PR 通过 qgw-pr-check.sh
