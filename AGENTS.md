# AGENTS.md

## What this repo is

通用 AI 技能仓库。提供质量门禁工作流和技能优化框架，可被任何项目复用。

## Repo structure

```
quality-dev-skills/
├── skills/
│   ├── quality-gate-workflow/   # 质量门禁工作流
│   └── skill-optimizer/         # 技能自动优化框架
├── shared/
│   └── skill-template/          # 新技能模板
└── scripts/                     # 安装/管理脚本
```

## Key facts for agents

- **通用技能** — 不绑定任何项目，可被任何项目使用
- **项目扩展** — 项目通过 `.qgw/` 覆盖机制添加项目专属内容
- **Symlink 安装** — 软链接到 `~/.agents/skills/`，源文件修改立即生效

## Install / update

```bash
bash scripts/install.sh                    # install all
bash scripts/install.sh quality-gate-workflow  # install one
bash scripts/install.sh --update           # update (re-link)
```
