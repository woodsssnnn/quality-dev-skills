# 评分规则

技能质量评估的 9 条规则。每条规则有 ID、检查内容、权重和自动修复标记。

## 规则列表

### 1. description_trigger

**检查**: description 是否以 "Use when" 开头

**权重**: 0.15

**自动修复**: ✓

**通过标准**:
```yaml
description: |-
  Use when [具体场景]. Triggers on: [关键词列表].
```

**失败示例**:
```yaml
description: |-
  这个技能用于...  # 缺少 "Use when" 开头
```

---

### 2. no_workflow_in_desc

**检查**: description 不包含工作流步骤

**权重**: 0.15

**自动修复**: ✓

**通过标准**:
- description 中不含 "Step 1"、"步骤"、"流程" 等流程性词汇
- description 只描述触发场景，不描述执行过程

**失败示例**:
```yaml
description: |-
  Use when optimizing skills. Step 1: analyze, Step 2: score...  # 包含步骤
```

---

### 3. token_efficiency

**检查**: SKILL.md 行数 < 500

**权重**: 0.10

**自动修复**: ✗

**通过标准**:
- 主文件 SKILL.md 不超过 500 行
- 详细内容放 references/ 目录

**失败示例**:
- SKILL.md 有 600+ 行

---

### 4. reference_depth

**检查**: 外部引用不超过一层深

**权重**: 0.10

**自动修复**: ✗

**通过标准**:
- 排除 skill 内部引用（`./references/`、`references/`、`../`）
- 排除脚本引用（`./scripts/`）
- 排除目录引用（以 `/` 结尾）
- 排除 HTTP 链接
- 其他外部引用不超过 1 层

**失败示例**:
```markdown
- [外部文档](external/sub/doc.md)  # 两层深，且不在 skill 内部
```

---

### 5. no_anti_patterns

**检查**: 无时效性时间信息、无魔法数字

**权重**: 0.15

**自动修复**: ✗

**通过标准**:
- 不含时效性日期（如 "截至 2026-06-15"、"有效期至..."）
- 允许文档性日期（变更日志、脚本验证时间戳）
- 不含无上下文的独立数字（规则编号、版本号除外）
- 不含超过 2 层的外部文件引用（见 reference_depth 规则）

**失败示例**:
```markdown
截至 2026-06-15，需要执行 3 次检查...  # 时效性日期 + 魔法数字
```

**允许示例**:
```markdown
v2.3（2026-06-11）：根据流水线第 3 次挂...  # 文档性日期，合法
verifiedDate: '2026-06-11'  # 脚本验证时间戳，合法
```

---

### 6. has_checklist

**检查**: 工作流有检查清单或编号步骤

**权重**: 0.10

**自动修复**: ✗

**通过标准**:
- 至少有一个有序列表（1. 2. 3.）或检查清单（- [ ]）
- 步骤之间有明确的先后关系

**失败示例**:
- 全是段落文字，没有结构化步骤

---

### 7. has_progress_output

**检查**: 步骤有入口/出口日志

**权重**: 0.10

**自动修复**: ✗

**通过标准**:
- 关键步骤有输出格式定义
- 如 "输出: 技能结构摘要"、"计算 baseline score"

**失败示例**:
- 步骤描述只有动作，没有产出物

---

### 8. rationalization_table

**检查**: 有反模式反驳表

**权重**: 0.10

**自动修复**: ✗

**通过标准**:
- 有一个表格列出常见反模式和正确做法
- 格式: | 反模式 | 正确做法 |

**失败示例**:
- 没有任何反模式说明

---

### 9. clear_gates

**检查**: pass/fail 标准明确

**权重**: 0.05

**自动修复**: ✗

**通过标准**:
- 有明确的 "通过条件" 和 "失败条件"
- 如 "val_score > baseline 才接受"

**失败示例**:
- 只说 "优化到满意为止"，没有量化标准

---

## 评分计算

```python
total_score = sum(rule_weight * rule_pass for rule in rules)
# 每条规则: pass=1.0, fail=0.0
# 总分范围: 0.0 ~ 1.0
```

## 分数解读

| 分数范围 | 等级 | 说明 |
|---------|------|------|
| 0.9 - 1.0 | A | 优秀，符合 best-practices |
| 0.7 - 0.9 | B | 良好，有改进空间 |
| 0.5 - 0.7 | C | 及格，需要优化 |
| < 0.5 | D | 不及格，需要重写 |

---

## 动态层（项目级规则）

> 静态层 9 条规则来自 `shared/agent-skills-best-practices.md`，适用于所有技能。
> 动态层从项目实际经验中提取规则，仅影响项目内技能评分。

### 加载机制

1. 检查项目 `.qgw/config.json` 是否声明了 `dev_rule.path`
2. 如存在，读取 `dev_rule.path`/SKILL.md 的进化日志章节
3. 提取出现次数 ≥ 3 的 AP 条目，转化为动态评分规则

### 动态规则格式

```python
# 从 AP-NNN 条目生成
dynamic_rules = [
    {
        "id": f"dyn_{ap_id}",
        "name": ap_title.lower().replace(" ", "_"),
        "check": f"代码中是否违反: {ap_pattern}",
        "weight": 0.10,
        "source": f"project-dev-rule AP-{ap_id} (出现{ap_count}次)",
        "auto_fix": False
    }
]
```

### 动态规则属性

| 属性 | 值 | 说明 |
|------|-----|------|
| `weight` | 0.10 | 固定权重（与静态规则同等重要） |
| `auto_fix` | False | 动态规则不自动修复，只提供建议 |
| `scope` | 项目内 | 仅影响当前项目的技能评分 |

### 示例

假设 project-dev-rule 中有：
```
### AP-003: SQL 字段别名未验证
- 出现次数: 4
- 反模式: 后端 SQL SELECT 别名指向错误列
```

转化为动态规则：
```python
{
    "id": "dyn_ap_003",
    "name": "sql_field_alias_verified",
    "check": "SQL SELECT 别名是否与实际 DB 列名对齐",
    "weight": 0.10,
    "source": "project-dev-rule AP-003 (出现4次)"
}
```

---

## 自进化技能特殊评分

当评估目标是 `project-dev-rule` 本身时，使用特殊评分规则：

| 规则 | 静态层行为 | 特殊处理 |
|------|---------|----------|
| 3. `token_efficiency` | SKILL.md < 500 行 | **跳过**：自进化技能允许超过 500 行 |
| 6. `has_checklist` | 有有序列表或检查清单 | **特殊检查**：进化日志是否有结构化表格 |
| 8. `rationalization_table` | 有反模式反驳表 | **特殊检查**：反模式教训章节是否有“正确做法”字段 |

### 新增：进化完整性规则

| ID | 检查内容 | 权重 |
|----|---------|------|
| `evolution_log_exists` | 进化日志章节非空（有表头行） | 0.05 |
| `rules_have_sources` | 每条 CR/AP 规则有来源、日期、验证方式字段 | 0.10 |
| `no_bloat` | 核心规则 ≤ 50 条 | 0.05 |

这三条规则仅在评估 project-dev-rule 时生效，不影响其他技能评分。
