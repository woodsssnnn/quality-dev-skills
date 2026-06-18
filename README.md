# quality-dev-skills

[English](README.en.md) | 中文

通用 AI 技能仓库。提供质量门禁工作流、技能优化框架和项目技能模板，可被任何项目复用。

## 包含的技能

| 技能 | 说明 |
|------|------|
| `quality-gate-workflow` | 质量门禁工作流（需求→Plan→代码全链路验证） |
| `skill-optimizer` | 技能自动优化框架 |

## 模板

| 模板 | 说明 |
|------|------|
| `project-dev-rule-template` | 项目开发规范技能模板（AI会话内生成） |

## 安装

```bash
git clone https://gitcode.com/songnan/quality-dev-skills.git ~/quality-dev-skills
cd ~/quality-dev-skills
bash scripts/install.sh
```

## 项目集成

本仓库是 **Base 层**，完全独立，不依赖任何项目层。

### 双层架构

```
Base 层 (quality-dev-skills)          Project 层 (project-dev-skills)
├── quality-gate-workflow              ├── project-dev-rule (AI生成)
├── skill-optimizer                    └── project-deploy
└── project-dev-rule-template/
```

### 项目技能生成

1. 在项目空间启动AI会话
2. 读取 `shared/project-dev-rule-template/INDEX.md`
3. AI根据模板+项目上下文生成 `project-dev-rule`
4. 更新 `CLAUDE.md` / `AGENTS.md` 约束

### 项目覆盖

项目层通过 `.qgw/` 覆盖机制添加项目专属内容，不修改 base 层文件。

## 版本管理

### 版本信息

```bash
# 查看当前版本
cat version.json | grep version

# 检查版本兼容性
bash scripts/check-compatibility.sh -t 1.0.0 -p 1.0.0
```

### 更新项目技能

```bash
# 更新project-dev-rule到最新版本
bash scripts/update-project-skill.sh /path/to/project
```

## 多平台支持

本项目支持多种AI编码工具平台：

| 平台 | 适配器 | 安装方式 |
|------|--------|----------|
| **Claude Code** | `platforms/claude-code/` | 插件安装 |
| **Codex** | `platforms/codex/` | 插件安装 |
| **OpenCode** | `platforms/opencode/` | 服务器插件 |
| **MiMoCode** | `platforms/minocode/` | 插件安装 |
| **通用** | `platforms/general/AGENTS.md` | 复制AGENTS.md |

详见 [多平台兼容方案](#多平台支持)。

## 更新

```bash
cd ~/quality-dev-skills
git pull
bash scripts/install.sh --update
```
