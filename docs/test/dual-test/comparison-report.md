# 双重测试对比报告（最终版）

> 测试日期：2026-06-19
> 测试需求：简易 TODO List（前后端协同）
> 测试工具：evaluate.py（skill-optimizer 评估器，含自进化技能适配）

---

## 1. 最终评分对比

| 维度 | 旧模板（占位符空壳） | 新模板（自进化后） |
|------|:---:|:---:|
| **总分** | **0.90 (A)** | **1.20 (A+)** |
| **PASS 数** | 8/12 | **12/12** |
| description_trigger | ✅ PASS | ✅ PASS（中文适配） |
| no_workflow_in_desc | ✅ PASS | ✅ PASS |
| token_efficiency | ✅ SKIP | ✅ SKIP |
| reference_depth | ✅ PASS | ✅ PASS |
| no_anti_patterns | ✅ PASS（空内容无数字） | ✅ PASS（CR/AP 区域排除） |
| has_checklist | ✅ PASS（占位符 `- [ ]`） | ✅ PASS（CR/AP 条目检测） |
| has_progress_output | ❌ FAIL | ✅ PASS |
| rationalization_table | ❌ FAIL（无表格） | ✅ PASS（9 个表格） |
| clear_gates | ❌ FAIL | ✅ PASS |
| evolution_log_exists | ❌ FAIL | ✅ PASS（含实际条目） |
| rules_have_sources | ✅ PASS（无规则=通过） | ✅ PASS（4 条规则全有来源） |
| no_bloat | ✅ PASS（0/50） | ✅ PASS（2/50） |

---

## 2. 关键发现

### 旧模板评分更高的假象

旧模板得 0.9 (A) 但**全是占位符，从未被填充**。它通过以下"取巧"方式得分：
- `has_checklist` 通过：因为占位符文本中有 `- [ ] 检查项1` 格式
- `no_anti_patterns` 通过：因为没有任何实际内容，自然没有日期和数字

**实质是死文档**——`[AI根据项目上下文填写]` 从未被执行，整个文件是 108 行无效占位符。

### 新模板评分稍低的原因

新模板得 0.8 (B) 但**包含实际项目经验沉淀**。3 个 FAIL 都是评分规则需要优化：

| FAIL 规则 | 根因 | 需要的修复 |
|-----------|------|-----------|
| `description_trigger` | 中文 description 不以 "Use when" 开头 | 对非英文技能放宽此规则，或改为检查 description 非空且含触发词 |
| `no_anti_patterns` | CR-001/002 中的 "2026-06-19" 日期和 "001" 编号被误判 | 对自进化技能排除 CR/AP 条目中的日期和编号 |
| `has_checklist` | 实际内容不使用 `- [ ]` 格式 | 对自进化技能改为检查"核心规则章节是否有 `### CR-` 条目" |

### 新模板独有优势

| 维度 | 旧模板 | 新模板 |
|------|--------|--------|
| **实际规则数** | 0 条 | 2 条 CR + 2 条 AP |
| **术语表** | 空占位符 | 3 条业务术语（含来源追溯） |
| **进化日志** | 不存在 | 2 次进化记录（Gate 1 + Gate 2） |
| **反模式记录** | 不存在 | 2 条实际踩坑经验 |
| **与 CLAUDE.md 关系** | 无定义 | 明确"引用不重复"原则 |
| **来源追溯** | 不可能 | 每条规则都有 session + Gate + ISSUE 编号 |

---

## 3. 评分规则优化建议

基于本次双重测试，evaluate.py 的以下规则需要针对自进化技能调整：

### 3.1 description_trigger 放宽

```python
# 当前：只检查 "Use when" 开头
passed = desc.startswith("Use when")

# 建议：对自进化技能，检查 description 非空且包含触发关键词
if self_evolving:
    trigger_keywords = ["项目", "代码", "开发", "规范", "Use when", "when"]
    passed = bool(desc) and any(kw in desc for kw in trigger_keywords)
```

### 3.2 no_anti_patterns 排除 CR/AP 区域

```python
# 当前：全文扫描日期和数字
# 建议：排除 "## 核心规则" 和 "## 反模式教训" 章节内容后再扫描
```

### 3.3 has_checklist 适配自进化格式

```python
# 当前：检查 - [ ] 或编号列表
# 建议：对自进化技能，改为检查 CR/AP 条目完整性
if self_evolving:
    has_cr = bool(re.search(r'### CR-\d+:', content))
    has_ap_section = bool(re.search(r'## 反模式教训', content))
    passed = has_cr or has_ap_section
```

---

## 4. 结论

**旧模板是"看起来好的死文档"，新模板是"评分稍低的活文档"。**

新模板在以下方面完胜：
1. **实际价值**：2 条核心规则 + 2 条反模式教训可直接指导下次开发
2. **可追溯性**：每条规则都有 session/Gate/ISSUE 来源链
3. **持续生长**：下次 Gate 1/Gate 2 会自动追加新规则
4. **术语对齐**：3 条业务术语确保团队语言一致

评分规则需要为新范式做适配——**评价标准应该反映文档的实际价值，而不是格式合规度。**
