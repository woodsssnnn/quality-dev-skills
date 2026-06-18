# 安装 Quality Dev Skills

以下步骤面向 AI Agent。请按顺序执行。

## Step 0: 克隆仓库

```bash
git clone https://gitcode.com/songnan/quality-dev-skills.git ~/quality-dev-skills
cd ~/quality-dev-skills
```

## Step 1: 安装技能

### Linux / macOS / Git Bash

```bash
bash scripts/install.sh
```

### Windows PowerShell

```powershell
.\scripts\install.ps1
```

## Step 2: 验证安装

检查以下目录存在且包含 `SKILL.md`：

- `~/.agents/skills/quality-gate-workflow/SKILL.md`
- `~/.agents/skills/skill-optimizer/SKILL.md`

```bash
ls -la ~/.agents/skills/
```

## Step 3: 告知用户

- 安装了哪些技能
- 安装位置（`~/.agents/skills/`，软链接方式）
- 如何使用（技能会在 AI Agent 对话中自动触发）
- 如何更新（`git pull` 后无需重装，源文件修改立即生效）
