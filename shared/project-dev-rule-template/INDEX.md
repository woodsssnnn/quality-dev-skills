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
