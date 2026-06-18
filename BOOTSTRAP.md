# Quality Dev Skills 安装引导

> 本文档面向 AI Agent。当你要使用通用质量技能但发现未安装时，按以下步骤操作。

## 前置检查

```bash
ls ~/.agents/skills/quality-gate-workflow/SKILL.md 2>/dev/null && echo "已安装" || echo "未安装"
```

## 安装步骤

### Step 1: 定位仓库

```bash
find ~ -maxdepth 3 -name "quality-dev-skills" -type d 2>/dev/null
```

### Step 2: 执行安装

```bash
cd ~/quality-dev-skills
bash scripts/install.sh
```

### Step 3: 验证

```bash
ls ~/.agents/skills/quality-gate-workflow/SKILL.md
ls ~/.agents/skills/skill-optimizer/SKILL.md
```

## 使用

安装后，在 AI Agent 对话中使用参数触发 quality-gate-workflow：

| 场景 | 命令 |
|------|------|
| 从 PRD 写计划 | `根据PRD写计划 --gate1` |
| 按计划实现代码 | `实现SP1 --gate2` |
| 全流程 | `全流程 --all` |
| 复盘会话质量 | `复盘 --self` |
| 一致性分析 | `分析 --analyze` |
