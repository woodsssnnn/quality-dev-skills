# Agent Skills 最佳实践指南

> 综合 Anthropic（Claude）、OpenAI（Codex）及 Agent Skills 开放标准（agentskills.io）的官方最佳实践，指导编写高质量、可复用的 AI 技能。

---

## 1. 核心原则

### 1.1 简洁为王

上下文窗口是共享资源。你的 Skill 与系统提示词、对话历史、其他 Skill 元数据共享同一窗口。

**默认假设：AI 已经足够聪明。** 只提供 AI 不知道的信息。对每条内容自问：

- "AI 真的需要这个解释吗？"
- "这段话值得消耗的 token 吗？"

**好例子（~50 tokens）：**

```markdown
## 提取 PDF 文本

使用 pdfplumber 提取文本：

​```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
​```
```

**坏例子（~150 tokens）：**

```markdown
## 提取 PDF 文本

PDF（便携式文档格式）是一种常见的文件格式，包含文本、图片等内容。
要提取 PDF 中的文本，你需要使用一个库。有很多可用的 PDF 处理库，
但 pdfplumber 是推荐的，因为它易于使用并且能很好地处理大多数情况。
首先，你需要使用 pip 安装它。然后你可以使用下面的代码...
```

简洁版本假设 AI 知道什么是 PDF 和库怎么用。

### 1.2 设定适当的自由度

根据任务的脆弱性和可变性，匹配指令的具体程度。

| 自由度 | 适用场景 | 示例 |
|--------|---------|------|
| **高自由** | 多种方案均可、依赖上下文判断 | 代码审查流程、分析报告 |
| **中自由** | 有推荐模式、允许一定变化 | 生成报告、数据转换 |
| **低自由** | 操作脆弱易错、一致性关键、有固定顺序 | 数据库迁移、部署脚本 |

**比喻：** 把 AI 想象成一个在路径上探索的机器人：

- **悬崖窄桥：** 只有一条安全路径 → 提供具体护栏和精确指令（低自由）
- **开阔旷野：** 多条路径通向成功 → 给出大方向，信任 AI 找到最佳路线（高自由）

### 1.3 跨模型测试

Skill 的效果依赖于底层模型。测试你计划使用的所有模型：

- **Haiku（快速经济）：** Skill 是否提供了足够的引导？
- **Sonnet（平衡）：** Skill 是否清晰高效？
- **Opus（深度推理）：** Skill 是否避免了过度解释？

---

## 2. 文件结构规范

### 2.1 标准目录结构

```
skill-name/
├── SKILL.md              # 必需：元数据 + 指令
├── scripts/              # 可选：可执行脚本
│   ├── analyze.py        # 工具脚本
│   └── validate.py       # 验证脚本
├── references/           # 可选：详细文档
│   ├── finance.md        # 领域文档
│   └── sales.md          # 领域文档
├── assets/               # 可选：模板、资源
│   └── template.xlsx     # 模板文件
└── agents/
    └── openai.yaml       # 可选（Codex）：UI 配置和依赖声明
```

### 2.2 SKILL.md 格式

每个 SKILL.md 由两部分组成：YAML Frontmatter + Markdown 正文。

```markdown
---
name: my-skill-name
description: 清晰描述这个 Skill 做什么以及什么时候使用它
---

# My Skill Name

## 指令
[清晰、分步骤的指引]

## 示例
[具体的使用示例]
```

### 2.3 Frontmatter 字段规范

| 字段 | 必需 | 约束 |
|------|------|------|
| `name` | 是 | 最长 64 字符，仅小写字母/数字/连字符，不能以连字符开头或结尾，不能包含连续连字符，不能包含 `anthropic`/`claude` 保留词 |
| `description` | 是 | 最长 1024 字符，非空，描述做什么+何时使用 |
| `license` | 否 | 许可证名称或引用 |
| `compatibility` | 否 | 最长 500 字符，环境需求说明 |
| `metadata` | 否 | 任意键值对，用于扩展属性 |
| `allowed-tools` | 否 | 空格分隔的预批准工具列表（实验性） |

---

## 3. 命名规范

### 3.1 命名模式

使用一致的命名模式，推荐 **动名词形式**（verb + -ing），清晰描述 Skill 提供的活动或能力。

| 类型 | 示例 | 推荐度 |
|------|------|--------|
| **动名词** | `processing-pdfs`、`analyzing-spreadsheets`、`testing-code` | 推荐 |
| 名词短语 | `pdf-processing`、`spreadsheet-analysis` | 可接受 |
| 动作导向 | `process-pdfs`、`analyze-spreadsheets` | 可接受 |

### 3.2 避免的命名

- 模糊名称：`helper`、`utils`、`tools`
- 过于泛化：`documents`、`data`、`files`
- 保留词：`anthropic-helper`、`claude-tools`
- 集合内命名不一致

---

## 4. 编写高质量 Description

`description` 是 Skill 发现的主要机制。AI 从可能 100+ 个 Skill 中使用它来选择正确的 Skill。

### 4.1 核心规则

1. **始终使用第三人称。** description 被注入系统提示词，不一致的人称会导致发现问题。
2. **具体并包含关键词。** 同时描述做什么和何时使用的触发词。
3. **前置核心用例和触发词。** 当安装大量 Skill 时，description 可能被截断，前置确保关键信息不丢失。
4. **绝不总结技能的工作流。** 测试表明，当 description 概括了技能的流程步骤时，AI 可能直接跟随 description 而跳过阅读技能正文——导致遗漏关键细节。description 只写"何时使用"，不写"怎么用"。

```yaml
# 错误：总结了工作流 — AI 可能跳过技能正文
description: Use when executing plans - dispatches subagent per task with code review between tasks

# 正确：只有触发条件，无工作流摘要
description: Use when executing implementation plans with independent tasks in the current session
```

### 4.2 好的示例

```yaml
# PDF 处理
description: 从 PDF 文件提取文本和表格，填写表单，合并文档。当处理 PDF 文件或用户提及 PDF、表单、文档提取时使用。

# Excel 分析
description: 分析 Excel 电子表格，创建数据透视表，生成图表。当分析 Excel 文件、电子表格、表格数据或 .xlsx 文件时使用。

# Git 提交助手
description: 通过分析 git diff 生成描述性提交信息。当用户要求帮助编写提交信息或审查暂存的更改时使用。
```

### 4.3 坏的示例

```yaml
description: 帮助处理文档
description: 处理数据
description: 处理文件相关的事情
```

---

## 5. 渐进式披露（Progressive Disclosure）

这是 Skill 架构的核心机制，确保只加载所需内容。

### 5.1 三级加载

| 级别 | 加载时机 | Token 消耗 | 内容 |
|------|---------|-----------|------|
| **L1：元数据** | 始终（启动时） | ~100 tokens/Skill | `name` 和 `description` |
| **L2：指令** | Skill 被触发时 | 建议 < 5000 tokens | SKILL.md 正文 |
| **L3：资源** | 按需加载 | 实际上无限制 | 脚本输出、引用文件等 |

### 5.2 实用规则

- SKILL.md 正文**控制在 500 行以内**
- 接近限制时拆分到独立文件
- 引用文件保持 **SKILL.md 下一层**，禁止深层嵌套

### 5.3 组织模式

**模式 1：高层指南 + 引用**

```markdown
# PDF 处理

## 快速开始
[基本用法直接写在 SKILL.md]

## 高级功能
- **表单填写**：参见 [FORMS.md](FORMS.md)
- **API 参考**：参见 [REFERENCE.md](REFERENCE.md)
- **示例**：参见 [EXAMPLES.md](EXAMPLES.md)
```

**模式 2：按领域组织**

```
bigquery-skill/
├── SKILL.md (概览和导航)
└── reference/
    ├── finance.md (收入、计费指标)
    ├── sales.md (商机、管线)
    ├── product.md (API 使用、功能)
    └── marketing.md (活动、归因)
```

**模式 3：条件细节**

```markdown
# DOCX 处理

## 创建文档
使用 docx-js 创建新文档。参见 [DOCX-JS.md](DOCX-JS.md)。

## 编辑文档
简单编辑直接修改 XML。
- **修订追踪**：参见 [REDLINING.md](REDLINING.md)
- **OOXML 详情**：参见 [OOXML.md](OOXML.md)
```

### 5.4 引用深度规则

**好：** SKILL.md 直接引用所有文件（一层深度）

```
SKILL.md → advanced.md
SKILL.md → reference.md
SKILL.md → examples.md
```

**坏：** 嵌套引用（AI 可能只部分读取）

```
SKILL.md → advanced.md → details.md → actual_info.md
```

### 5.5 长引用文件加目录

超过 100 行的引用文件，在顶部添加目录：

```markdown
# API 参考

## 目录
- 认证和设置
- 核心方法（创建、读取、更新、删除）
- 高级功能（批量操作、Webhooks）
- 错误处理模式
- 代码示例
```

---

## 6. 工作流和反馈循环

### 6.1 复杂任务用工作流

将复杂操作分解为清晰的顺序步骤。提供清单让 AI 跟踪进度：

```markdown
## 研究综合工作流

复制此清单并跟踪进度：

​```
研究进度：
- [ ] 步骤 1：阅读所有源文档
- [ ] 步骤 2：识别关键主题
- [ ] 步骤 3：交叉引用声明
- [ ] 步骤 4：创建结构化摘要
- [ ] 步骤 5：验证引用
​```

**步骤 1：阅读所有源文档**
审查 `sources/` 目录中的每个文档...

**步骤 2：识别关键主题**
寻找跨来源的模式...
```

### 6.2 实现反馈循环

**常见模式：** 运行验证器 → 修复错误 → 重复

```markdown
## 文档编辑流程

1. 编辑 `word/document.xml`
2. **立即验证**：`python scripts/validate.py unpacked_dir/`
3. 如果验证失败：
   - 仔细查看错误信息
   - 修复 XML 中的问题
   - 再次运行验证
4. **验证通过后才继续**
5. 重新打包：`python scripts/pack.py unpacked_dir/ output.docx`
```

### 6.3 条件工作流模式

```markdown
## 文档修改工作流

1. 判断修改类型：
   - **创建新内容？** → 跟随「创建工作流」
   - **编辑已有内容？** → 跟随「编辑工作流」

2. 创建工作流：
   - 使用 docx-js 库
   - 从零构建文档

3. 编辑工作流：
   - 解包已有文档
   - 直接修改 XML
   - 每次更改后验证
```

---

## 7. 内容编写指南

### 7.1 避免时效性信息

**坏：**
```markdown
如果你在 2025 年 8 月之前做这个，使用旧 API。
2025 年 8 月之后，使用新 API。
```

**好：**
```markdown
## 当前方法
使用 v2 API 端点：`api.example.com/v2/messages`

## 旧模式
<details>
<summary>旧版 v1 API（已于 2025-08 废弃）</summary>
v1 API 使用：`api.example.com/v1/messages`，此端点不再受支持。
</details>
```

### 7.2 使用一致术语

选择一个术语并在整个 Skill 中保持一致：

| 好的一致 | 坏的不一致 |
|---------|-----------|
| 始终用 "API endpoint" | 混用 "API endpoint"、"URL"、"API route"、"path" |
| 始终用 "field" | 混用 "field"、"box"、"element"、"control" |
| 始终用 "extract" | 混用 "extract"、"pull"、"get"、"retrieve" |

### 7.3 提供模板和示例

**严格模板（API 响应、数据格式等）：**

```markdown
## 报告结构

始终使用以下精确模板：

​```markdown
# [分析标题]

## 执行摘要
[关键发现的一段式概述]

## 关键发现
- 发现 1 及支持数据
- 发现 2 及支持数据
​```
```

**灵活模板（需要适应性时）：**

```markdown
## 报告结构

以下是合理的默认格式，但请根据分析类型做出最佳判断：

[模板内容...]

根据具体分析类型调整章节。
```

**输入/输出示例对：**

```markdown
## 提交信息格式

按以下示例生成提交信息：

**示例 1：**
输入：添加了基于 JWT 令牌的用户认证
输出：
​```
feat(auth): 实现 JWT 认证

添加登录端点和令牌验证中间件
​```
```

---

## 8. 脚本编写规范

### 8.1 解决问题，不要推给 AI

**好：** 显式处理错误
```python
def process_file(path):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        print(f"File {path} not found, creating default")
        with open(path, "w") as f:
            f.write("")
        return ""
    except PermissionError:
        print(f"Cannot access {path}, using default")
        return ""
```

**坏：** 推给 AI 处理
```python
def process_file(path):
    return open(path).read()  # 让 AI 去想办法
```

### 8.2 避免魔法数字

**好：**
```python
# HTTP 请求通常在 30 秒内完成，更长超时应对慢速连接
REQUEST_TIMEOUT = 30
# 三次重试平衡可靠性和速度
MAX_RETRIES = 3
```

**坏：**
```python
TIMEOUT = 47  # 为什么是 47？
RETRIES = 5   # 为什么是 5？
```

### 8.3 提供工具脚本

即使 AI 能自己写脚本，预制脚本更有优势：

- 比生成的代码更可靠
- 节省 token（不需要在上下文中包含代码）
- 节省时间（不需要代码生成）
- 确保跨使用场景的一致性

**明确执行意图：**

```markdown
- **执行脚本**（最常见）：`运行 analyze_form.py 提取字段`
- **作为参考读取**（用于复杂逻辑）：`参见 analyze_form.py 了解提取算法`
```

### 8.4 可验证的中间输出

对于复杂任务，使用 "计划-验证-执行" 模式：

1. 分析 → **创建计划文件** → **验证计划** → 执行 → 验证

这通过结构化格式的计划文件 + 验证脚本，在应用更改前捕获错误。

---

## 9. 迭代开发流程

### 9.1 评估驱动开发

1. **识别差距：** 不用 Skill 让 AI 执行代表性任务，记录具体失败
2. **创建评估：** 构建 3 个测试场景
3. **建立基线：** 不用 Skill 测量 AI 表现
4. **编写最小指令：** 只创建解决差距所需的内容
5. **迭代：** 执行评估，对比基线，改进

### 9.2 双实例迭代法

最有效的 Skill 开发流程涉及两个 AI 实例：

- **Claude A（专家）：** 帮助设计和改进 Skill
- **Claude B（代理）：** 使用 Skill 执行实际任务

**创建新 Skill：**

1. 不用 Skill 完成一次任务，注意你反复提供的信息
2. 识别可复用模式
3. 让 Claude A 创建 Skill
4. 审查简洁性："删除 AI 已知内容的解释"
5. 优化信息架构
6. 用 Claude B 在类似任务上测试
7. 基于观察迭代

**改进现有 Skill：**

1. 在真实工作流中使用 Skill
2. 观察 Claude B 的行为（在哪里挣扎/成功）
3. 带着具体观察回到 Claude A
4. 审查建议并应用
5. 再次测试
6. 持续循环

### 9.3 观察 AI 如何使用 Skill

注意：

- **意外的探索路径：** 文件读取顺序出乎意料？结构可能不够直观
- **遗漏的关联：** AI 没有跟随重要文件的引用？链接可能需要更显眼
- **过度依赖某些部分：** 反复读取同一文件？考虑移到 SKILL.md
- **被忽略的内容：** 从不访问的文件？可能不需要或信号不够强

---

## 10. 验证技能有效性（TDD 适配）

技能文档和代码一样需要测试。"没有观察到 AI 在没有技能时失败，就不知道技能教了正确的东西。"

### 10.1 红-绿-重构循环

| TDD 概念 | 技能验证 |
|----------|---------|
| **测试用例** | 带 AI 子代理的压力场景 |
| **测试失败（红）** | AI 在没有技能时违反规则（基线行为） |
| **测试通过（绿）** | AI 在有技能时遵守规则 |
| **重构** | 发现新的合理化借口 → 堵住 → 重新验证 |

### 10.2 基线测试（红）

在没有技能的情况下让 AI 执行代表性任务，逐字记录：
- 它做了什么选择？
- 它使用了什么合理化借口（原文）？
- 哪些压力触发了违规？

这是"先写测试再写代码"的等价物。

### 10.3 合理化借口表

从基线测试中捕获 AI 使用的每个借口，明确反驳：

```markdown
| 借口 | 现实 |
|------|------|
| "太简单不值得测试" | 简单的代码也会出错。测试只需 30 秒。 |
| "我后面再测试" | 测试立即通过什么也证明不了。 |
| "这个情况不同，因为……" | 这正是合理化借口的标志。 |
```

### 10.4 不同技能类型的测试方式

| 技能类型 | 测试重点 | 成功标准 |
|---------|---------|---------|
| 纪律执行类（规则/要求） | 压力场景下是否遵守 | 最大压力下仍遵循规则 |
| 技术类（操作指南） | 边界情况、缺失信息 | 正确应用到新场景 |
| 模式类（心智模型） | 识别何时适用/不适用 | 正确识别和判断 |
| 参考类（文档/API） | 信息检索和正确应用 | 找到并正确使用信息 |

---

## 11. OpenAI Codex 特有补充

### 10.1 Skill 发现位置

| 范围 | 位置 | 建议用途 |
|------|------|---------|
| REPO | `$CWD/.agents/skills` | 团队共享，微服务/模块级别 |
| REPO | `$REPO_ROOT/.agents/skills` | 仓库根级共享 |
| USER | `$HOME/.agents/skills` | 个人跨仓库通用 |
| ADMIN | `/etc/codex/skills` | 机器级默认 |
| SYSTEM | Codex 内置 | 通用 Skill |

### 10.2 agents/openai.yaml 配置

```yaml
interface:
  display_name: "用户可见名称"
  short_description: "简短描述"
  icon_small: "./assets/small-logo.svg"
  icon_large: "./assets/large-logo.png"
  brand_color: "#3B82F6"
  default_prompt: "默认提示词"

policy:
  allow_implicit_invocation: false  # false 时仅支持显式调用

dependencies:
  tools:
    - type: "mcp"
      value: "serverName"
      description: "描述"
      transport: "streamable_http"
      url: "https://example.com/mcp"
```

### 10.3 OpenAI 额外最佳实践

- 每个 Skill 聚焦**一个任务**
- 优先使用**指令**而非脚本（除非需要确定性行为或外部工具）
- 编写**命令式步骤**，明确输入和输出
- 用提示词测试 Skill description 确认触发行为正确
- 上下文预算：Skill 初始列表约占上下文窗口的 2%（或 8000 字符），description 过多时会被截断

---

## 12. 反模式清单

| 反模式 | 正确做法 |
|--------|---------|
| Windows 路径 `scripts\helper.py` | 始终用正斜杠 `scripts/helper.py` |
| 提供太多选择 "你可以用 A 或 B 或 C..." | 提供默认方案 + 逃生舱口 |
| 嵌套引用 A→B→C→D | 从 SKILL.md 直接引用，一层深度 |
| SKILL.md 超过 500 行 | 拆分到独立文件 |
| 时效性信息直接写在正文 | 用 "旧模式" 折叠区块 |
| 术语不一致 | 统一用一个词 |
| 模糊的 description | 具体描述做什么 + 何时用 + 触发词 |
| 第一人称 description | 始终第三人称 |
| 假设工具已安装 | 明确声明依赖和安装命令 |
| 魔法数字 | 所有常量有注释说明原因 |
| 脚本推给 AI 处理错误 | 显式错误处理 |
| description 总结了工作流 | description 只写触发条件，不写流程步骤 |
| 存根文件（3-10 行仅一句话） | 合并为 catalog.md 表格文件 |
| 多语言双版本脚本维护（.js + .ps1） | 统一到单一跨平台版本 |
| 检查脚本无退出码 | FAIL 级必须 `process.exit(1)`，支持 CI gate |
| 过时 backup 文件保留不删 | 合并到新结构后删除，不保留"旧版参考" |

---

## 13. 发布前检查清单

### 核心质量

- [ ] description 具体并包含关键词
- [ ] description 同时描述做什么和何时使用
- [ ] description 不包含工作流摘要（只有触发条件）
- [ ] SKILL.md 正文在 500 行以内
- [ ] 额外详情在独立文件中（如需要）
- [ ] 无时效性信息（或在"旧模式"区块中）
- [ ] 全文术语一致
- [ ] 示例具体，非抽象
- [ ] 文件引用一层深度
- [ ] 渐进式披露使用得当
- [ ] 工作流有清晰步骤

### 代码和脚本

- [ ] 脚本解决问题而非推给 AI
- [ ] 错误处理显式且有帮助
- [ ] 无魔法数字（所有值有理由）
- [ ] 需要的包已列出并验证可用
- [ ] 脚本有清晰文档
- [ ] 无 Windows 路径（全部正斜杠）
- [ ] 关键操作有验证/验证步骤
- [ ] 质量关键任务包含反馈循环

### 测试

- [ ] 至少 3 个评估场景
- [ ] 在 Haiku、Sonnet、Opus 上测试
- [ ] 在真实使用场景中测试
- [ ] 团队反馈已整合（如适用）

---

## 参考来源

| 来源 | 链接 |
|------|------|
| Anthropic 官方 Skill 概述 | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview |
| Anthropic Skill 编写最佳实践 | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices |
| Anthropic 官方 Skill 仓库 | https://github.com/anthropics/skills |
| OpenAI Codex Skills 文档 | https://developers.openai.com/codex/skills |
| OpenAI Codex 最佳实践 | https://developers.openai.com/codex/learn/best-practices |
| Agent Skills 开放标准 | https://agentskills.io/specification |
