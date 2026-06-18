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
