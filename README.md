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

## 致谢

本项目的设计与实现借鉴了以下开源项目的理念与实践，在此向所有贡献者致以诚挚的感谢：

| 项目 | 借鉴内容 | 本项目中的应用 |
|------|---------|---------------|
| **[planning-with-files](https://github.com/nicepkg/planning-with-files)** | 5问题重启测试、2-Action Rule、3-Strike Error Protocol | 通用工作协议（`general-protocols.md`）、会话恢复机制 |
| **[Spec Kit](https://github.com/nicepkg/spec-kit)** | `/speckit.clarify` 结构化澄清、`/speckit.analyze` 交叉分析 | 需求澄清机制（多选题模式）、`--analyze` 跨 artifact 分析 |
| **[agent-spec](https://github.com/nicepkg/agent-spec)** | boundary enforcement、`stamp` 命令 | Gate 2 Step 2.5 变更范围检查、Git Trailer 可追溯性 |
| **[Autonoma](https://github.com/nicepkg/autonoma)** | agentic testing（静态+动态双层验证） | Gate 2 S4 静态验证 + S4.5 E2E 行为验证 |
| **[Ponytail](https://github.com/nicepkg/ponytail)** | YAGNI 检查清单 | PM 顾问 D6 维度：功能必要性、标准库替代、原生特性替代 |
| **[OpenSpec](https://github.com/nicepkg/openspec)** | delta specs（只描述变更部分） | `--incremental` 增量验证模式 |
| **[Python](https://www.python.org/)** | Python 3 标准库 | gate-enforcer.py、evaluate.py、verify-checkpoint.sh 的 JSON 解析与状态机实现 |
| **[JSON Schema](https://json-schema.org/)** | JSON Schema Draft-07 | acceptance-criteria-schema.json 验收清单格式规范 |

### 平台兼容致谢

本项目的多平台支持得益于以下平台的开放生态：

- **[Claude Code](https://claude.ai/)** (Anthropic) — Hooks 机制、SKILL.md 规范
- **[Codex](https://openai.com/)** (OpenAI) — 服务器插件架构
- **[OpenCode](https://github.com/opencode)** — 服务器插件接口
- **[MiMoCode](https://mimo.org/)** — 插件安装规范

> 本项目的核心理念：将社区最佳实践沉淀为可复用的 AI 技能，让每个开发者都能站在巨人的肩膀上。
