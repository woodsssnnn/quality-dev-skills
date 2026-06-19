# project-dev-rule-template

## 模板说明

本项目模板用于生成**自进化**的项目开发规范技能（project-dev-rule）。

**设计理念**：
- **极简骨架**：初始只有 ~50 行，6 个空章节，不预设内容
- **过程驱动进化**：通过 Gate 1/Gate 2 的实际开发过程自动沉淀术语、规则和反模式教训
- **引用不重复**：CLAUDE.md/AGENTS.md 已有的项目整体约束只引用不复制
- **冲突以事实为准**：当规则与 CLAUDE.md 冲突时，以代码调查事实为最高优先级

## 与其他组件的关系

```
qgw-init (Step 4.5) ──生成──→ project-dev-rule/SKILL.md
                                     │
Gate 1 P5-evolve ────沉淀术语/规则───→│
Gate 2 S5-evolve ──沉淀反模式/升级───→│
                                     │
advisor-templates ←─注入 DEV_RULE_SUMMARY
skill-optimizer ←──读取进化日志作为动态评分规则
reference_skills ←──只读参考（如 -dev-rule）
```

详见 `shared/skill-protocol.md` 的技能协同关系和 `skills/quality-gate-workflow/references/knowledge-compounding.md` 的完整闭环图。

## 使用方式

### 方式一：qgw-init 自动初始化（推荐）

```bash
# 在项目空间执行 qgw-init，Step 4.5 会自动生成 project-dev-rule
--init
```

### 方式二：脚本初始化

```bash
cd ~/quality-dev-skills
bash scripts/init-project-skill.sh /path/to/project
```

## 模板结构

```
project-dev-rule-template/
├── INDEX.md                          # 本文件
├── structure/                        # 目录结构骨架
│   ├── SKILL.md.skeleton             # 极简技能骨架（~50 行）
│   ├── glossary.md.template          # 术语表模板
│   └── evolution-log.md.template     # 进化日志模板
├── references/                       # 参考文档
│   └── evolution-protocol.md         # 进化协议（规则格式/触发条件/升级规则）
├── hooks/                            # 生命周期 hooks
│   ├── on-create.sh                  # 新项目初始化
│   ├── on-update.sh                  # 模板更新触发
│   ├── on-optimize.sh                # 优化触发
│   └── on-session-start.sh           # 会话启动钩子（含进化状态显示）
└── scripts/
    └── check-yagni.sh                # YAGNI 检查
```

## 进化协议摘要

| 章节 | 内容 | 填充时机 |
|------|------|---------|
| 项目身份 | 项目名、技术栈、构建命令 | qgw-init Step 4.5 |
| 核心规则 | 编号 CR-001+，从 Gate 过程沉淀 | Gate 1 P5-evolve / Gate 2 S5-evolve |
| 反模式教训 | 编号 AP-001+，从 FAIL/BUG 提炼 | Gate 2 S5-evolve |
| 术语表 | 业务术语中英文+定义 | Gate 1 P1 需求解析 |
| 参考资源 | 声明的上游技能列表 | qgw-init Step 4.5 |
| 进化日志 | 变更摘要表 | 每次 evolve 自动追加 |

完整协议见 `references/evolution-protocol.md`。

## 版本信息

| 字段 | 值 |
|------|-----|
| 模板版本 | 2.0.0 |
| 兼容项目版本 | ≥0.8.0.0 |
| 最后更新 | 2026-06-18 |

### 更新日志

- **v2.0.0**：自进化架构重写
  - 从 237 行占位符模板重写为 ~50 行极简骨架
  - 新增进化协议（CR/AP 编号体系、触发条件、升级规则、膨胀控制）
  - 新增术语表和进化日志模板
  - hooks 增加进化状态显示
  - 与 CLAUDE.md/AGENTS.md 建立"引用不重复"关系
- **v1.0.0**：初始开源发布
  - 项目开发规范技能模板
  - AI 会话内生成流程
  - Hooks 机制
  - YAGNI 检查
  - 强度级别系统（lite/full/ultra/off）

## 相关文档

- [进化协议](references/evolution-protocol.md) - 规则格式和进化机制
- [技能间通信协议](../skill-protocol.md) - 技能协同关系
- [知识复利机制](../../skills/quality-gate-workflow/references/knowledge-compounding.md) - 完整闭环图
# project-dev-rule-template

## 模板说明

本模板是 project-dev-rule 技能的骨架，用于在项目空间生成项目特定的开发规范技能。

**设计理念**：
- 模板只提供结构和索引，实际内容由AI在项目会话内生成
- 遵循"宪法式"设计：明确约束，AI遵守一致性
- 支持双循环进化：项目经验可反哺模板更新

## 使用方式

### 方式一：AI会话内生成（推荐）

1. 在项目空间启动AI会话
2. 读取本模板的 INDEX.md
3. AI根据模板+项目上下文生成完整技能
4. 写入 `.agents/skills/project-dev-rule/`
5. 更新 `CLAUDE.md` / `AGENTS.md` 约束

### 方式二：脚本初始化

```bash
cd ~/quality-dev-skills
bash scripts/init-project-skill.sh /path/to/project
```

## 模板结构

```
project-dev-rule-template/
├── INDEX.md              # 本文件，说明模板用法
├── structure/            # 目录结构骨架
│   ├── SKILL.md.skeleton # 技能骨架（只有框架）
│   └── references/       # 参考文档占位
│       ├── backend/
│       ├── frontend/
│       └── business/
├── prompts/              # 生成提示词
│   ├── generate-backend.md
│   ├── generate-frontend.md
│   └── generate-business.md
├── hooks/                # 生命周期hooks
│   ├── on-create.sh      # 新项目初始化
│   ├── on-update.sh      # 模板更新触发
│   ├── on-optimize.sh    # 优化触发
│   └── on-session-start.sh  # 🆕 会话启动钩子
└── scripts/              # 🆕 检查脚本
    └── check-yagni.sh    # YAGNI检查
```

## 生成约束

AI在生成project-dev-rule时必须遵守：

1. **单一职责**：一个技能做一件事
2. **清晰接口**：明确输入输出
3. **封装上下文**：知识打包在技能内
4. **无隐藏依赖**：显式声明依赖
5. **确定性优先**：能脚本化的不留给AI

## 生成流程

```
读取本INDEX.md
    ↓
检查项目配置（project.yaml）
    ↓
加载SKILL.md.skeleton
    ↓
根据prompts/中的指南生成内容
    ↓
写入 .agents/skills/project-dev-rule/
    ↓
更新CLAUDE.md/AGENTS.md绑定
    ↓
触发hooks/on-create.sh
```

## 版本信息

| 字段 | 值 |
|------|-----|
| 模板版本 | 1.0.0 |
| 兼容项目版本 | ≥1.0.0 |
| 最后更新 | 2026-06-17 |

### 更新日志

- **v1.0.0**：初始开源发布
  - 项目开发规范技能模板
  - AI 会话内生成流程
  - Hooks 机制
  - YAGNI 检查
  - 强度级别系统（lite/full/ultra/off）

## 相关文档

- [SKILL.md.skeleton](structure/SKILL.md.skeleton) - 技能骨架
- [生成提示词](prompts/) - AI生成指导
- [生命周期hooks](hooks/) - 自动化流程
