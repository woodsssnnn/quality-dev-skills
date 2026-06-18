# Self-Check 工作流详细步骤

手动触发的技能执行质量复盘。不修改任何文件，只产出报告。

## 目录
- [SC0：定位会话](#sc0定位会话)
- [SC1：提取 QGW 日志](#sc1提取-qgw-日志)
- [SC2：检查 Verifier 执行](#sc2检查-verifier-执行)
- [SC3：检查文件产物](#sc3检查文件产物)
- [SC4：分析 Plan 质量](#sc4分析-plan-质量)
- [SC5：生成报告](#sc5生成报告)

---

## SC0：定位会话

> 输出: `[qgw:self:SC0] 定位会话 ...` / `✅ 找到: {sessionName}` 或 `❌ 未找到`

### 输入方式

- `--self` → 定位当前项目下最近的 QGW session
- `--self <session-id>` → 直接定位指定 ID
- `--self <keyword>` → 在 session 名称中搜索关键词

### 定位方法（优先读 docs/sessions/）

**优先级 1：读 `docs/sessions/INDEX.md`**

```
1. 检查 docs/sessions/INDEX.md 是否存在
2. 存在 → 从 Session Registry 表中定位目标 session
3. 读取 docs/sessions/{session-id}.md → 获取完整执行记录
```

**优先级 2：读 `docs/QGW-INDEX.md`**

```
1. 检查 docs/QGW-INDEX.md 是否存在
2. 存在 → 从 Active Sessions 表中定位目标 session
3. 读取对应的 verification JSON → 获取验收数据
```

**优先级 3：JSONL fallback**（向后兼容）

当 `docs/sessions/` 和 `docs/QGW-INDEX.md` 都不存在时，降级到 JSONL 解析：

```bash
# 按 session-id 直接定位
ls ~/.claude/projects/*/{sessionId}.jsonl

# 按关键词定位（解析 JSONL 的 custom-title 行）
grep -l "customTitle.*keyword" ~/.claude/projects/*/*.jsonl

# 定位最近的 QGW 会话（包含 qgw 日志）
grep -l "qgw:" ~/.claude/projects/*/*.jsonl | xargs ls -t | head -1
```

找到后记录：session ID、session name、文件路径、文件大小、最后修改时间。

---

## SC1：提取 QGW 日志

> 输出: `[qgw:self:SC1] 提取 QGW 日志 ...` / `✅ N 条日志`

### 优先读 Session Summary

**优先级 1：读 `docs/sessions/{session-id}.md`**

```
1. 检查 docs/sessions/{session-id}.md 是否存在
2. 存在 → 解析 Execution Flow 表构建步骤覆盖矩阵
3. 解析 Decisions 表获取跳过理由和 ISSUE 响应
4. 解析 Bug Log 获取修复记录
5. 解析 Traceability 获取 codeRefs + commitSha
```

**优先级 2：JSONL fallback**（向后兼容）

当 session summary 不存在时，降级到 JSONL 解析：

```bash
grep "qgw:" {jsonl-path} | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        obj = json.loads(line)
        msg = obj.get('message', {})
        content = msg.get('content', '')
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get('type') == 'text':
                    text = block['text']
                    if '[qgw:' in text:
                        print(text[:300])
        elif isinstance(content, str) and '[qgw:' in content:
            print(content[:300])
    except: pass
"
```

### 步骤覆盖分析

根据提取的日志构建覆盖矩阵：

```
Gate 1: P0? P1? P1.5? P1.6? P1.7? P2? P2.5? P3? P4? P5?
Gate 2: S0? S1? S2? S3? S3.5? S4? S5?
Debug:  D1? D2? D3? D4?
Audit:  A? B? C? D? E?
```

缺失步骤 = 潜在问题。

---

## SC2：检查 Verifier 执行

> 输出: `[qgw:self:SC2] 检查 Verifier ...` / `✅ N 次 verifier 派发` 或 `❌ 未发现 verifier 派发`

从 JSONL 中检查是否有实际的 Task/Agent 工具调用用于 verifier 派发。

**检查项**：

| # | 检查项 | PASS 条件 |
|---|--------|----------|
| 1 | P4/S4 是否有 Task 或 Agent 工具调用 | JSONL 中有 tool_use 且 name 为 Task/Agent |
| 2 | toolCallId 是否写入 | JSONL 中有 toolCallId 非空记录 |
| 3 | verifier 是否报告结果 | JSONL 中有 COVERED/PASS 等结论 |

**注意**：仅输出日志文本而没有实际工具调用 = 未执行。这是 anti-pattern #1。

---

## SC3：检查文件产物

> 输出: `[qgw:self:SC3] 检查文件产物 ...` / `✅ 全部存在` 或 `⚠️ N 项缺失`

检查工作空间目录和文件是否存在：

```bash
# 目录检查
ls -d docs/plans docs/verification docs/reports 2>&1

# JSON 文件检查
ls docs/verification/unit-*.json 2>/dev/null
ls docs/verification/error-patterns.json 2>/dev/null

# Plan 文件检查
ls docs/plans/*.md 2>/dev/null
```

**检查项**：

| # | 检查项 | PASS 条件 |
|---|--------|----------|
| 1 | `docs/plans/` 目录存在 | ls 返回目录 |
| 2 | `docs/verification/` 目录存在 | ls 返回目录 |
| 3 | Plan 文件存在 | 至少一个 .md 文件 |
| 4 | 验收 JSON 存在 | 至少一个 unit-*.json |
| 5 | error-patterns.json | 存在即 PASS，不存在 ⚠️ 降级 |
| 6 | Plan 文件末尾有验收清单附录 | grep "Acceptance Criteria" |

---

## SC4：分析 Plan 质量

> 输出: `[qgw:self:SC4] 分析 Plan 质量 ...` / `✅ N 个 unit, M 条标准` 或 `⚠️ K 条标准过于模糊`

读取 `docs/plans/` 下的 Plan 文件，分析验收标准质量。

### 质量检查规则

| # | 规则 | 模糊示例 | 具体示例 |
|---|------|---------|---------|
| 1 | 组件类型必须写明具体组件 | "有筛选器" | "筛选器=流程树多选组件" |
| 2 | 字段存在必须写明具体字段 | "字段正确" | "跟进人页面无审核人字段" |
| 3 | 标签文本必须写明确切文本 | "列名正确" | "列标题='引发何种不良后果'" |
| 4 | 必填/默认必须写明控制条件 | "时间可填" | "计划完成时间必填受配置控制" |
| 5 | 每条标准必须追溯到源 §X.X | 无引用 | "(§6.1.1)" |
| 6 | PRD 枚举项必须逐个说明 | "默认处理" | 每项单独列出处理方式 |
| 7 | dev-rule pattern 是否指定 | 无 pattern | "用 5.0-crud-module 模式" |

### 检查方法

```bash
# 检查是否有 PRD 章节引用
grep -c "§" docs/plans/*.md

# 检查是否有模糊描述
grep -iE "(有.*功能|字段.*正确|列名.*正确|默认.*处理)" docs/plans/*.md
```

---

## SC5：生成报告

> 输出: `[qgw:self:SC5] 生成报告` / `✅ 报告完成` 或 `❌ N 项问题 (--strict)`

### 报告格式

```markdown
## QGW 自检报告
会话: {sessionName} ({sessionId})
日期: {date}
触发参数: {原始参数}

### 执行概览
| 维度 | 状态 |
|------|------|
| Gate 1 步骤覆盖 | P0✅ P1✅ P2✅ P3✅ P4❌ P5❌ |
| Gate 2 步骤覆盖 | S0✅ S1✅ S2✅ S3✅ S3.5— S4❌ S5❌ |
| Verifier 执行 | ❌ 未派发 |
| 文件产物 | ⚠️ docs/verification/ 未创建 |
| 验收标准质量 | ⚠️ 2 条模糊 / 8 条具体 |

### 发现问题
| # | 严重性 | 问题 | 涉及步骤 | 修复建议 |
|---|--------|------|---------|---------|
| 1 | ❌ 高 | P4 verifier 未实际派发 | Gate 1 P4 | 确认 Task/Agent 工具调用 |
| 2 | ⚠️ 中 | docs/verification/ 未创建 | Gate 1 P0 | 添加 P0 自动初始化 |
| 3 | ⚠️ 中 | 验收标准 #3 过于模糊 | Gate 1 P1 | "有筛选功能" → "筛选器=流程树多选(§6.1.1)" |

### 改进建议
- [ ] {从问题列表推导的具体改进项}
```

### `--strict` 模式

当使用 `--self --strict` 时：
- 任何 ❌ 高严重性问题 → 整体 FAIL，输出 `[qgw:self:SC5] ❌ FAIL — N 项高严重性问题`
- 任何 ⚠️ 中严重性问题 → 列出但不阻断
- 无任何问题 → `✅ PASS`

不使用 `--strict` 时，只出报告不判 FAIL。
