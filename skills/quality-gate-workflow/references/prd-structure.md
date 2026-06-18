# PRD 目录结构与全内容解析规范

## PRD 必须是目录

PRD 不是单个文件，而是一个包含所有需求资产的目录。这支持增量更新和多类型文件管理。

### 目录规范

```
docs/prd/{feature}/
├── README.md                  # 主 PRD 文档（入口，含版本号、目录索引）
├── revision-log.md            # 修订历史汇总表
├── images/                    # 原型图、截图、流程图、UI 设计稿
│   ├── ui-mockup-login.png
│   └── flow-approval.png
├── tables/                    # 数据字典、枚举定义、字段映射表、决策矩阵
│   └── data-dictionary.md
├── attachments/               # 补充文档、会议纪要、邮件截图、竞品分析
│   └── stakeholder-feedback.md
└── proposals/                 # PRD 修订提案（由 RV 工作流生成）
    └── prp-{date}-{简述}.md
```

### README.md Frontmatter

```yaml
---
prd-version: v1.0.0.0
created: 2026-06-01
last-revised: 2026-06-18
revision-count: 0
status: active              # active | archived
sections:
  - id: "§2.1"
    name: 用户注册
    assets: [images/ui-register.png]
  - id: "§2.2"
    name: 用户登录
    assets: [images/ui-login.png, tables/auth-rules.md]
  - id: "§3.1"
    name: 性能要求
    assets: []
---
```

### 命名规则

| 类型 | 命名格式 | 示例 |
|------|---------|------|
| PRD 目录 | `{feature-name}/` | `user-auth/`、`payment-module/` |
| 图片 | `{type}-{描述}.{ext}` | `ui-mockup-login.png`、`flow-approval.svg` |
| 表格 | `{描述}.md` 或 `.csv` | `data-dictionary.md`、`enum-values.csv` |
| 附件 | `{描述}.{ext}` | `stakeholder-feedback.md`、`competitor-analysis.pdf` |
| 修订提案 | `prp-{YYYY-MM-DD}-{简述}.md` | `prp-2026-06-18-section-2-3-fix.md` |

---

## 全内容解析规则（Gate 1 P1 增强）

Gate 1 P1 解析 PRD 时，**必须处理目录中的所有资产**，不可只读取文字。

### 1. 文字解析

- 逐段提取可验证项，每项追溯到 `§X.X`
- 识别业务规则、约束条件、枚举项
- 每个枚举项（角色/类型/选项）必须逐个说明处理方式

### 2. 图片/原型图解析

```
处理流程：
1. 使用 Read 工具读取图片文件
2. 提取 UI 元素：按钮、表单、列表、弹窗、导航
3. 提取交互流程：页面跳转、状态变化、条件分支
4. 提取数据展示：字段名称、格式要求、校验规则
5. 与文字描述交叉验证（一致性检查）
6. 图片中的业务规则记录到对应 §X.X 的可验证项
```

**关键要求**：
- 原型图中的字段名、按钮文案、状态名称都是需求的一部分
- 图片中出现的枚举值（如下拉选项）必须在可验证项中体现
- 图片与文字不一致时：生成结构化澄清 → 记录到 `_clarifications.md`

### 3. 表格/数据字典解析

```
处理流程：
1. 逐行提取字段定义：字段名、类型、约束、默认值
2. 提取枚举值域：每个枚举项的含义和约束
3. 提取关联关系：外键、引用、依赖
4. 每个字段对应到涉及的可验证项
5. 数据字典中的约束条件（如唯一性、非空）必须体现在验收标准中
```

### 4. 附件解析

```
处理流程：
1. 阅读补充文档，提取隐含约束和业务规则
2. 会议纪要中的决策点必须记录到对应章节
3. 与主文档交叉验证，发现矛盾则生成澄清
4. 竞品分析中的差异化要求必须体现在验收标准中
```

### 5. 交叉验证矩阵

P1 完成后输出交叉验证矩阵：

```markdown
## PRD 交叉验证矩阵

| §X.X | 文字 | 图片 | 表格 | 附件 | 一致性 |
|------|------|------|------|------|--------|
| §2.1 用户注册 | ✅ 12项 | ✅ ui-register.png 已解析 | ✅ data-dict 3字段 | — | ✅ 一致 |
| §2.2 用户登录 | ✅ 8项 | ⚠️ ui-login.png 与文字不一致 | ✅ data-dict 2字段 | — | ⚠️ 需澄清 |
```

---

## P0 PRD 引导式创建

Gate 1 P0 检测 PRD 状态，按以下流程处理：

### 场景 A：PRD 目录已就绪

```
if docs/prd/{feature}/ 是目录且含 README.md:
    → ✅ 正常处理，进入 P1 全内容解析
```

### 场景 B：PRD 是单文件（旧格式）

```
elif PRD 路径指向单文件:
    → ⚠️ 提示用户：“检测到 PRD 是单文件格式，需要转为目录格式”
    → 提供迁移辅助：
      1. 自动创建 docs/prd/{feature}/ 目录结构
      2. 将单文件移为 README.md
      3. 提示用户补充 images/tables/attachments
    → 迁移完成后再继续 Gate 1
```

### 场景 C：无 PRD（引导式创建）

```
else:
    → 📝 进入引导式创建流程（见下方）
```

**引导式创建流程**：

```
📝 当前项目没有需求文档目录。让我帮你创建：

请告诉我这次需求的标题（如“用户认证模块”、“支付系统”），
我会自动创建对应的 PRD 目录结构。
```

**步骤 1**：用户提供需求标题

**步骤 2**：QGW 自动创建目录结构

```bash
# 根据标题生成 kebab-case 目录名
docs/prd/{feature-name}/
├── README.md              # 预填标题和基础 frontmatter
├── revision-log.md        # 初始版本记录
├── images/                # 空目录，等待放入原型图/截图
├── tables/                # 空目录，等待放入数据字典/规则表
├── attachments/           # 空目录，等待放入补充文档
└── proposals/             # 空目录，用于后续 PRD 修订提案
```

README.md 预填内容：
```yaml
---
prd-version: v1.0.0.0
created: {today}
last-revised: {today}
revision-count: 0
status: draft
sections: []
---

# {需求标题}

> 请将需求文档内容放入本目录：
> - 主文档内容直接写在本文件中
> - 原型图/截图放入 images/ 目录
> - 数据字典/规则表放入 tables/ 目录
> - 补充文档放入 attachments/ 目录
```

**步骤 3**：提示用户放入文档

```
✅ PRD 目录已创建：docs/prd/{feature-name}/

现在请将需求文档放入对应目录：
- 📄 主文档内容 → 直接写入 README.md
- 🖼️ 原型图/截图 → 放入 images/ 目录
- 📊 数据字典/规则表 → 放入 tables/ 目录
- 📎 补充文档 → 放入 attachments/ 目录

放入完成后告诉我，我会开始解析需求并制定开发计划。
```

**步骤 4**：用户确认后，QGW 检查目录内容并进入 P1

```
用户确认后：
1. 扫描目录，列出发现的所有文件
2. 如果 README.md 仍为模板内容（无实质需求）→ 提醒用户填写
3. 如果目录为空（无任何文件）→ 提醒用户至少提供 README.md
4. 内容就绪 → 更新 frontmatter sections 字段 → 进入 P1 全内容解析
```

### 场景 D：用户跳过 PRD（不推荐）

```
用户明确选择跳过:
    → ⚠️ 警告：无 PRD 将导致以下后果：
      - 验收标准无法追溯到需求章节
      - verifier 无法检查 PRD→Plan 覆盖度
      - --analyze 的 AC1 检查将跳过
    → 创建最小骨架 PRD（仅标题，sections 为空）
    → 进入 Gate 1，但 P1 仅基于用户口述需求提取可验证项
    → 反模式 #6（需求猜测）仍然适用：不可自行脑补未说明的需求
```

---

## P0/S0 工作空间初始化

Gate 1 P0 和 Gate 2 S0 初始化时，确保 `docs/prd/` 目录存在：

```bash
mkdir -p docs/prd
```

如果项目有多个 feature，每个 feature 一个子目录：
```
docs/prd/
├── user-auth/
├── payment-module/
└── notification-system/
```

---

## 反模式

- **#9**（升级）：PRD 全内容解析是强制要求。未读取图片/表格 = 未完整解析需求。PRD 必须是目录格式。
- **#57**：PRD 使用单文件格式而非目录格式。
