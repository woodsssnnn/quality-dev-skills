# Quality Dev Skills

质量门禁工作流和项目开发规范技能集合。

## 技能清单

| 技能 | 触发参数 | 说明 |
|------|----------|------|
| `quality-gate-workflow` | `--gate1` / `--gate2` / `--all` | 质量门禁工作流（需求→Plan→代码全链路验证） |
| `skill-optimizer` | `--optimize` | 技能自动优化框架 |
| `qgw-init` | `--init` | 项目初始化引导（7 步交互式） |
| `api-design-review` | `--api-review` | REST API 设计审查门禁 |
| `db-migration-gate` | `--db-migration` | 数据库迁移质量门禁 |

## 参数矩阵

### 核心参数

| 参数 | 说明 |
|------|------|
| `--gate1` | Gate 1: 需求→Plan（提取验收标准、PM顾问、写Plan、Verifier） |
| `--gate2` | Gate 2: Plan→代码（实现、自验、Verifier、提交） |
| `--all` | 全流程 Gate 1+2 串行 |
| `--self` | 自检：复盘指定会话的Gate执行质量 |
| `--analyze` | Cross-Artifact 一致性分析 |

### 修饰参数

| 参数 | 说明 |
|------|------|
| `--strict` | 零偏差模式 |
| `--lite` | 轻量快速通道（跳过 P1.5/P1.6/P1.7） |
| `--incremental` | 增量验证（只验证变更部分） |
| `--e2e` | 启用 E2E 行为验证（S4.5） |
| `--fix` | 自动修复模式 |

### 引擎子命令

| 参数 | 说明 |
|------|------|
| `--prd-changed` | PRD 变更正向触发（cosmetic/minor/major 三级） |
| `--plan-tweak` | Gate 2 执行中轻量微调 Plan |
| `--init` | 项目 QGW 初始化引导 |
| `--optimize` | 技能质量优化 |
| `--api-review` | API 设计审查 |
| `--db-migration` | 数据库迁移安全检查 |

## 工作模式

| 模式 | 说明 |
|------|------|
| `prd` | 需求驱动（默认） |
| `bug` | Bug 修复 |
| `opt` | 技术优化 |
| `impl` | 纯实现 |
| `debug` | 调试模式 |
| `audit` | 审计模式 |

## 强度级别

| 级别 | 说明 |
|------|------|
| `lite` | 基础规范，适合快速开发 |
| `full` | 完整规范，适合生产环境（默认） |
| `ultra` | 严格规范，适合关键系统 |
| `off` | 关闭规范检查 |

切换: `/quality-dev-skills lite|full|ultra|off`

## 安装

```bash
git clone https://gitcode.com/songnan/quality-dev-skills.git ~/quality-dev-skills
cd ~/quality-dev-skills
bash scripts/install.sh
```

## 项目开发规范

在项目空间启动AI会话，执行：
```
读取 ~/quality-dev-skills/shared/project-dev-rule-template/INDEX.md，为本项目生成 project-dev-rule 技能
```

## 更多信息

- [README](../../README.md)
- [安装指南](../../INSTALL.md)
- [技能清单](../../skill-manifest.json)
# Quality Dev Skills

质量门禁工作流和项目开发规范技能集合。

## 核心技能

- **quality-gate-workflow**: 质量门禁工作流（需求→Plan→代码全链路验证）
- **skill-optimizer**: 技能自动优化框架
- **project-dev-rule-template**: 项目开发规范技能模板

## 使用方式

### 质量门禁工作流

```bash
# Gate 1: 需求→Plan
--gate1

# Gate 2: Plan→代码
--gate2

# 全流程
--all

# 自检
--self
```

### 项目开发规范

在项目空间启动AI会话，执行：
```
读取 ~/quality-dev-skills/shared/project-dev-rule-template/INDEX.md，为本项目生成 project-dev-rule 技能
```

## 安装

```bash
git clone https://gitcode.com/songnan/quality-dev-skills.git ~/quality-dev-skills
cd ~/quality-dev-skills
bash scripts/install.sh
```

## 更多信息

- [README](../../README.md)
- [安装指南](../../INSTALL.md)
