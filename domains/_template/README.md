# my-pack — 领域包模板

> 这是领域包脚手架。复制本目录（或跑 `python scripts/create-domain-pack.py <name>`），
> 把 `my-pack` 相关内容替换为你的领域内容。

## 目录约定

```
my-pack/
├── pack.json        # 包清单（id/version/兼容区间）—— 必需
├── governance.json  # 运行时配置增量（提示/验证命令/Bash 提示）—— 可选
├── rules/*.json     # 声明式规则集 —— 至少一个（领域包的核心价值）
└── README.md        # 本文件：说明适用范围、规则意图、维护约定
```

## 快速开始

1. 改 `pack.json`：`id`（kebab-case，与目录名一致）、名称、版本、兼容区间
2. 写 `rules/*.json`：每条规则 = 正则 + severity（block 阻断 / warn 提醒）+ 说清
   "为什么禁止、应该怎么改" 的 message（这是 agent 能自修的关键）
3. 校验：`python scripts/validate-domain-pack.py domains/my-pack`
4. 使用：项目 `.qgw/governance.json` 声明 `"packs": ["my-pack"]`，或复制到项目
   `.qgw/packs/my-pack/` 私有使用
5. 贡献回本仓库：提 PR（见仓库根 CONTRIBUTING.md「贡献领域包」）

## 规则书写要点

- **block 留给红线**：安全问题、破坏性 API、团队明确禁令；误报会消耗信任
- **warn 用于提醒**：风格/最佳实践类，注入提示但不打断
- **message 写修复路径**：不只说"禁止 X"，要说"用 Y 替代"
- 复杂检查用脚本逃生舱：`"script": "check-xxx.js"`（放本目录，约定见 spec）
- 同 id 规则集可被项目 `.qgw/rules/` 覆盖——领域包只提供基线，项目有最终裁量权
