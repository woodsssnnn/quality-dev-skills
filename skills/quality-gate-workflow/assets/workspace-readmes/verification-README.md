# docs/verification/ — 结构化验收数据

本目录存放质量门禁的结构化验收数据（JSON 格式）。

## 文件命名

与 `docs/plans/` 中的 Plan 文件同名，扩展名为 `.json`：

```
plans/feat-07-process-track.md    →  verification/feat-07-process-track.json
plans/BUG-2026-06-09-07-附件.md   →  verification/BUG-2026-06-09-07-附件.json
```

## JSON 结构

遵循 `~/.agents/skills/quality-gate-workflow/references/acceptance-criteria-schema.json` 定义的 schema。

核心字段：

```json
{
  "plan": "docs/plans/feat-07-process-track.md",
  "gate": 1,
  "generated": "2026-06-09",
  "units": [
    {
      "name": "维护列表筛选器",
      "items": [
        {"id": "U1-01", "spec": "筛选器=流程树多选", "source": "§6.1.1", "status": "PENDING"}
      ]
    }
  ],
  "verifierReports": [
    {"round": 1, "result": "PASS", "verifierType": "independent-verifier"}
  ]
}
```

## 状态流转

```
PENDING → PASS（验证通过）
PENDING → FAIL（验证失败，需附带 rootCause: CODE/PLAN）
FAIL    → PASS（修复后重新验证通过）
```

## 用途

- **Gate 2 Step 1**：读取 JSON 获取验收标准（避免重复提取）
- **verify-checkpoint.sh Hook**：提交前检查所有 item 是否 PASS
- **Knowledge Compounding**：分析 FAIL 模式，更新工作空间层 error-patterns.json

## 工作空间层 error-patterns.json

本目录可包含 `error-patterns.json`（工作空间层错误模式），格式如下：

```json
{
  "version": "1.0",
  "scope": "workspace",
  "project": "项目名称",
  "patterns": [
    {
      "id": "WP001",
      "category": "data-source",
      "description": "具体描述",
      "rootCauses": { "CODE": 2, "PLAN": 0 },
      "totalCount": 2,
      "lastSeen": "2026-06-09",
      "status": "active",
      "examples": ["具体例子"]
    }
  ],
  "upgradeLog": []
}
```

### 自进化流程

1. verifier 发现 FAIL → 自动提取模式 → 追加到本文件
2. 阈值升级（≥3/≥5/≥8 次） → 写入项目 CLAUDE.md 或项目 dev-rule skill
3. **不写全局** `references/error-patterns.json`（全局层需人工 promote）

### 与全局层的关系

- **本文件（工作空间层）**：项目特有模式，自动积累
- **`references/error-patterns.json`（全局层）**：跨项目通用模式，仅人工 promote
- 同一模式在 ≥3 个工作空间出现 → 代理建议 promote → 用户确认后写入全局
