# AGENTS.md

## What this repo is

通用 AI 技能仓库。提供**代码治理运行时（governance）**、流程级质量门禁工作流、
技能优化框架和领域包开放机制，可被任何项目复用。仓库保持中立——不包含任何
领域专属内容（领域规则经 domain pack 由社区贡献）。

## Repo structure

```
quality-dev-skills/
├── governance/                  # 代码级治理运行时（hooks 门禁/规则引擎/事件流/判题机）
│   ├── hooks/                   #   4 个 hook + lib（hook-input/config/rules/hint-state/integrity）
│   ├── rules/builtin/           #   内置中立规则集（密钥泄漏/调试残留）
│   ├── scripts/                 #   event-log/event-query/verify-links/blast-radius/...
│   ├── agents/                  #   reviewer/verifier/db-migrator 中立模板
│   └── tests/run-tests.js       #   自测（node governance/tests/run-tests.js）
├── skills/                      # 流程级技能
│   ├── quality-gate-workflow/   #   质量门禁工作流（PRD→Plan→Verifier）
│   ├── skill-optimizer/         #   技能自动优化框架
│   ├── prd-parse/               #   原始需求文档 1:1 解析
│   └── ...                      #   qgw-init + 垂直技能包
├── domains/
│   └── _template/               # 领域包脚手架（契约见 shared/domain-pack-spec.md）
├── shared/                      # 技能模板 + 领域包契约 + 协议
├── platforms/                   # 多平台适配
└── scripts/                     # 安装/管理/校验脚本
```

## Key facts for agents

- **中立性红线** — 仓库与提交记录不得出现任何来源项目品牌词；跑
  `bash scripts/check-banned-terms.sh` 自检（CI 同规则）
- **三层架构** — 项目 `.qgw/`（最高优先）> 领域包（`domains/<pack>/` 或项目
  `.qgw/packs/`）> Base 层内置默认；同 id 规则集/配置高优先级覆盖
- **governance 门禁** — 编辑文件命中 block 规则会 exit 2 喂回错误，必须修复
  后继续；规则是数据文件（`governance/rules/` 下 JSON），改规则不改代码
- **事件流** — `~/.zcode/governance-data/governance-events.jsonl` append-only
  哈希链；查询 `node governance/scripts/event-query.js --tail|--freq|--chain-verify`
- **项目扩展** — 项目通过 `.qgw/` 覆盖机制添加专属内容，不修改 base 层
- **Symlink 安装** — 软链接到 `~/.agents/skills/`，源文件修改立即生效

## Install / update

```bash
bash scripts/install.sh                    # install all skills
bash scripts/install.sh quality-gate-workflow  # install one
bash scripts/install.sh --update           # update (re-link)

# governance 门禁装配到某项目（在目标项目根目录执行）
node <repo>/governance/scripts/install-hooks.js
```

## 提交前自检

```bash
bash scripts/check-banned-terms.sh                     # 中立性
node governance/tests/run-tests.js                     # 治理运行时
python scripts/validate-domain-pack.py domains/<pack>  # 领域包（如有改动）
python scripts/generate-manifest.py --validate         # manifest 一致
```
