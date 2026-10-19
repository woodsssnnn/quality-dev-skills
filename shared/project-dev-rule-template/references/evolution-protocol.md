# Dev-Rule 进化协议

> 定义 project-dev-rule 的文件结构、规则格式、进化触发条件、升级规则和膨胀控制。
> 本协议被 quality-gate-workflow 的 P5-evolve 和 S5-evolve 步骤引用。

---

## 0. 文件结构（L2/L3 分离）

project-dev-rule 采用渐进式披露架构，SKILL.md 是 L2 索引层（始终精简），详细内容存储在 L3 文件中按需加载。

```
project-dev-rule/
├── SKILL.md              ← L2 索引层（~50 行，始终精简）
├── core-rules.md         ← L3 核心规则详情（Gate evolve 写入目标）
├── anti-patterns.md      ← L3 反模式教训详情（Gate evolve 写入目标）
├── glossary.md           ← L3 术语表详情（Gate evolve 写入目标）
├── evolution-log.md      ← L3 进化日志详情（Gate evolve 追加目标）
└── references/
    └── evolution-protocol.md  ← 本文件
```

**膨胀控制原理**：SKILL.md 只存索引表（规则计数 + 最近更新），详细内容增长在 L3 文件中。即使经过 100 次进化，SKILL.md 仍保持 ~50 行。

**L2 索引更新规则**：Gate evolve 写入 L3 文件后，同步更新 SKILL.md “规则索引”表的“条目数”和“最近更新”列。

### 0.1 L3 Divide and Conquer（借鉴 LLM-WIKI）

当单个 L3 文件超过 **200 行**（约 1200 词）时，触发拆分：

```
# 拆分前：
anti-patterns.md           ← 200+ 行

# 拆分后：
anti-patterns/
├── INDEX.md               ← 分类索引 + 每条一句话摘要
├── frontend.md            ← 前端相关反模式
├── backend.md             ← 后端相关反模式
└── integration.md         ← 前后端协同反模式
```

**拆分规则**：
1. **触发时机**：Gate evolve 写入前检查目标文件行数，≥ 200 行则先拆分再写入
2. **分类维度**：按技术领域（frontend/backend/integration）或按业务模块拆分
3. **INDEX.md 格式**：每条规则一行摘要（`### AP-NNN: [标题] → [子文件]`），便于快速定位
4. **SKILL.md 更新**：规则索引表的 L3 文件列更新为目录路径（`[anti-patterns/](./anti-patterns/INDEX.md)`）
5. **evaluate.py 适配**：扫描 L3 时需递归读取目录内所有 .md 文件

**各 L3 文件的拆分阈值和策略**：

| L3 文件 | 行数阈值 | 拆分维度 | 上限 |
|---------|:------:|---------|------|
| core-rules.md | 200 行 | 按技术领域 | 50 条（已有 consolidation） |
| anti-patterns.md | 200 行 | 按技术领域 | 无硬上限，拆分即可 |
| glossary.md | 100 行 | 按业务模块 | 无硬上限，拆分即可 |
| evolution-log.md | 100 行 | 按月归档 | 无硬上限，归档即可 |

---

## 1. 规则存储格式

### 1.1 核心规则（CR）

```markdown
### CR-NNN: [规则标题]
- **来源**: [session-id] / [Gate 1 P5-evolve | Gate 2 S5-evolve] / [ISSUE ID | FAIL ID]
- **日期**: YYYY-MM-DD
- **规则**: [具体规则描述]
- **反例**: [违反时的表现]
- **验证方式**: [如何检查合规]
```

**编号规则**：从 CR-001 开始递增，不跳号、不复用已删除编号。

### 1.2 反模式教训（AP）

```markdown
### AP-NNN: [反模式标题]
- **来源**: [session-id] / [Gate 2 S5-evolve] / [FAIL CODE-N | BUG ID]
- **日期**: YYYY-MM-DD
- **反模式**: [具体反模式描述]
- **正确做法**: [应该怎么做]
- **出现次数**: N
```

**编号规则**：从 AP-001 开始递增。出现次数 ≥ 3 时升级为 CR。

### 1.3 术语表

```markdown
| 术语 | 英文 | 定义 | 来源 |
|------|------|------|------|
| 流程穿透任务 | Process Track Task | [定义] | PRD §6.1 / session-xxx |
```

**来源格式**：`PRD §X.X` 或 `session-id / Gate 1 P1`。

---

## 2. 进化触发条件

### 2.1 Gate 1 P5-evolve（PM 视角沉淀）

| 触发条件 | 提取内容 | 写入章节 |
|---------|---------|---------|
| P1 可验证项包含业务术语 | 术语（中英文+定义） | glossary.md |
| P1.7 PM 顾问有被接受的 ISSUE | 需求理解规则 | core-rules.md |
| P2.5 架构师顾问有被接受的 ISSUE | 架构选型教训 | core-rules.md |
| P1 有澄清记录（_clarifications.md） | 业务歧义的确定性结论 | glossary.md |
| 架构师根因簇 ≥ 3 项 | 同根因升级为强制规则 | core-rules.md |

**提取规则**：
- 只提取**被接受**的 ISSUE（驳回的不写入）
- 只提取**重复出现**或**高严重性**的模式（单次 LOW 级 ISSUE 不写入）
- 每条规则必须包含来源 session ID、来源步骤、日期

### 2.2 Gate 2 S5-evolve（架构师视角沉淀）

| 触发条件 | 提取内容 | 写入章节 |
|---------|---------|---------|
| S4 verifier FAIL（CODE 根因） | 代码偏差模式 | anti-patterns.md |
| S4 横切检查 FAIL（CC-1~CC-6） | 横切失败模式 | anti-patterns.md |
| Debug 模式修复了 BUG | BUG 根因和修复模式 | anti-patterns.md |
| error-patterns frequency ≥ 3 | 升级为强制规则 | core-rules.md |
| P2.5 架构师 ISSUE 被接受（从 Gate 1 传递） | 技术债/模式选型教训 | core-rules.md |

---

## 3. 升级规则

反模式的渐进升级机制：

| 阶段 | 条件 | 存储位置 | 约束级别 |
|------|------|---------|---------|
| **教训** | 首次 FAIL | AP 条目（出现次数=1） | 提示 |
| **反模式** | 同类 FAIL ≥ 2 次 | AP 条目（出现次数递增） | 警告 |
| **强制规则** | 同类 FAIL ≥ 3 次 | 升级为 CR 条目 | 阻断 |

**同类判定**：标题关键词重叠 ≥ 60%，或来源根因簇相同。

**升级操作**：
1. 在 core-rules.md 创建新 CR 条目
2. 在 anti-patterns.md 对应 AP 条目标注 `→ 已升级为 CR-NNN`
3. 更新 SKILL.md 规则索引表的条目数
4. evolution-log.md 记录升级事件

---

## 4. 膨胀控制

### 4.1 核心规则上限

- 核心规则总数上限 **50 条**
- 达到 45 条时输出预警：`[qgw:evolve] ⚠️ 核心规则接近上限（45/50），建议 consolidation`
- 达到 50 条时触发 consolidation

### 4.2 Consolidation 规则

1. **合并同类**：相同根因的 CR 合并为一条，反例列表追加
2. **淘汰过时**：对应代码已被重构或删除的 CR 标记为 `[DEPRECATED]`
3. **保留高频**：按引用频率（被后续 session 读取次数）排序，保留高频
4. **归档**：被淘汰的 CR 移入 `references/archived-rules.md`（如不存在则创建）

### 4.3 进化日志审计

每 10 次进化（`evolution_count % 10 == 0`）时输出摘要：
```
[qgw:evolve] 进化审计：CR {n}条 / AP {m}条 / 术语 {k}条
  最近 10 次进化来源：Gate 1 ({a}次) / Gate 2 ({b}次)
  建议：{consolidation 建议或"无需操作"}
```

---

## 5. 与 CLAUDE.md / AGENTS.md 的关系

### 5.1 引用不重复

- CLAUDE.md / AGENTS.md 中已有的项目整体约束（项目结构、Git 规范、构建命令等），project-dev-rule **只引用不重复**
- project-dev-rule 的"项目身份"章节写一行引用，不复制内容

### 5.2 冲突解决

当 project-dev-rule 的规则与 CLAUDE.md / AGENTS.md 冲突时：

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 1（最高） | 代码调查事实 | grep/读代码/查 DB 的实际结果 |
| 2 | project-dev-rule 核心规则 | 从实际开发经验中沉淀 |
| 3 | CLAUDE.md / AGENTS.md | 项目整体约束 |
| 4（最低） | 参考技能（团队自有规范技能） | 通用最佳实践 |

### 5.3 同步机制

- project-dev-rule 进化时**不自动修改** CLAUDE.md
- 如果 CR 条目与 CLAUDE.md 冲突，在 CR 条目标注 `⚠️ 与 CLAUDE.md 冲突，以本规则为准（代码事实）`
- 用户可手动将重要 CR 同步到 CLAUDE.md

---

## 6. 执行规则

### 6.1 P5-evolve 执行流程

1. 读取 `.qgw/config.json` 的 `dev_rule.path`
2. 读取 `dev_rule.path`/SKILL.md（L2 索引）
3. 从本次 Gate 1 产出中提取新规则（按 §2.1 触发条件表）
4. 读取对应 L3 文件（core-rules.md / glossary.md），grep 已有标题避免重复
5. 追加到对应 L3 文件
6. 更新 SKILL.md 规则索引表（条目数 + 最近更新）
7. 追加 evolution-log.md
8. 更新 frontmatter `evolution_count += 1`
9. 输出：`[qgw:gate1:P5-evolve] ✅ 新增 CR-{N}、术语 {M} 条`

无进化时：输出 `[qgw:gate1:P5-evolve] ✅ 本次无新增规则`，仍递增 `evolution_count`。

### 6.2 S5-evolve 执行流程

1. 读取 `.qgw/config.json` 的 `dev_rule.path`
2. 读取 `dev_rule.path`/SKILL.md（L2 索引）
3. 从本次 Gate 2 产出中提取新规则（按 §2.2 触发条件表）
4. 读取 anti-patterns.md，检查 AP 出现次数，达阈值执行升级（§3）
5. grep 已有标题避免重复
6. 追加到对应 L3 文件（anti-patterns.md / core-rules.md）
7. 更新 SKILL.md 规则索引表（条目数 + 最近更新）
8. 追加 evolution-log.md
9. 更新 frontmatter `evolution_count += 1`
10. 如参考资源中有相关 pattern，在规则中引用
11. 输出：`[qgw:gate2:S5-evolve] ✅ 新增 AP-{N}、升级 CR-{M}`

无进化时：输出 `[qgw:gate2:S5-evolve] ✅ 本次无新增规则`，仍递增 `evolution_count`。

---

## 7. Audit 纠错机制（借鉴 LLM-WIKI audit/ 模式）

当已沉淀的 CR/AP 规则被证明是**错误的**（如根因判错、代码重构后过时），通过结构化纠错流程修正，而不是简单删除。

### 7.1 纠错触发场景

| 场景 | 示例 | 来源 |
|------|------|------|
| 根因判错 | AP-003 的根因实际是配置问题而非代码问题 | Gate 2 S4 FAIL 复查 |
| 规则过时 | CR-002 对应的代码已被重构删除 | --self 复盘 |
| 与事实矛盾 | CR-001 与基线代码调查结果冲突 | 代码 grep 实证 |
| 用户纠正 | 用户明确指出某条规则有误 | 会话内反馈 |

### 7.2 纠错流程

1. **标记**：在对应 CR/AP 条目顶部追加 `> ⚠️ AUDIT: [原因] — [日期]`
2. **修正**：更新规则内容，保留原始内容的 `~~删除线~~` 作为历史
3. **记录**：在 evolution-log.md 追加一行 `| 日期 | session | Audit | 修正 CR-NNN: [原因] |` 
4. **不删除**：即使规则完全错误，也不删除条目，而是标记为 `[REVOKED]` 并说明原因

### 7.3 纠错示例

```markdown
### AP-001: 前端筛选 status=all 未映射到后端
> ⚠️ AUDIT: 根因修正 — 实际是后端 ORM 自动过滤空字符串，非 SQL 问题 — 2026-07-15
- **来源**: session-todo / Gate 2 S5-evolve / FAIL CODE-3
- **日期**: 2026-06-19
- **反模式**: ~~前端传 status=all 但后端 SQL 直接 WHERE status='all'~~ ORM 层过滤空字符串导致未传参
- **正确做法**: 后端 Service 层对 status=all 或空字符串时不添加 WHERE 条件
- **出现次数**: 1
```

### 7.4 evaluate.py 适配

审计标记不影响评分，但 `rules_have_sources` 检查会跳过 `[REVOKED]` 条目（不计入有效规则数）。
