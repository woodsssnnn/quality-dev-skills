# 领域包（Domain Pack）规范 v1

领域包让某个技术栈/团队把**自己的**门禁规则、提示、验证约定接入 governance
运行时，而不需要改运行时本身。本仓库保持中立——所有领域内容由社区以领域包
形式贡献（`domains/<pack-name>/`）或项目私有（`<project>/.qgw/packs/<pack-name>/`）。

## 解析与优先级

包的启用：项目 `.qgw/governance.json` 声明 `"packs": ["<name>", ...]`。

解析位置（前者优先）：

1. `<projectDir>/.qgw/packs/<name>/` — 项目私有覆写（可覆写同名社区包）
2. `<repoRoot>/domains/<name>/` — 本仓库的社区领域包

包名约束：`/^[A-Za-z0-9][A-Za-z0-9._-]*$/`（禁路径分隔与 `..`）。

生效优先级（高 → 低）：

```
项目 .qgw/rules/ + .qgw/governance.json
  > 领域包（按 packs 声明顺序，后者覆盖前者）
    > governance 内置默认（config.default.json + rules/builtin/）
```

同 id 规则集整体被高优先级覆盖；列表类配置（promptMessages/verifyCommands/
bashHints/hints）逐层拼接。

## 目录结构

```
<pack-name>/
├── pack.json        # 必需 — 包清单
├── governance.json  # 可选 — 运行时配置增量
├── rules/*.json     # 强烈建议 — 声明式规则集（领域包的核心价值）
├── scripts/         # 可选 — 脚本逃生舱规则引用的检查脚本
└── README.md        # 建议 — 适用范围/规则意图/维护约定
```

## pack.json（清单，必需）

```json
{
  "schemaVersion": 1,
  "id": "my-pack",
  "name": "人类可读名称",
  "version": "0.1.0",
  "description": "一句话说明",
  "author": "贡献者",
  "license": "MIT",
  "compatibility": { "minRuntime": "0.9.0.0", "maxRuntime": "1.0.0.0" }
}
```

约束：

- `id`：kebab-case，与目录名一致
- `version`：语义化版本（SemVer）
- `compatibility`：与 governance 运行时（本仓库 version.json 的 4 级版本号）
  的兼容区间；越界时运行时告警并拒绝加载（宁可不门禁，不可半生效）
- 凭据/内网地址/客户名**禁止**出现在包内任何文件（CI 禁词扫描覆盖 domains/）

## governance.json（配置增量，可选）

字段与合并语义同 `governance/config.default.json`（见 governance/README.md）。
领域包通常贡献：`promptMessages`（语境提示）、`verifyCommands`（本地验证命令
识别 → 机器凭证）、`bashHints`、`hints`。

## rules/*.json（规则集）

```json
{
  "id": "my-pack-rules",
  "version": "0.1.0",
  "description": "说明",
  "appliesTo": { "extensions": [".ts", ".java"] },
  "rules": [
    { "id": "R-001", "severity": "block", "pattern": "<JS 正则>",
      "flags": "i", "message": "为什么禁止 + 应该怎么改" },
    { "id": "R-002", "severity": "block", "script": "scripts/check-x.js",
      "message": "复杂检查（脚本逃生舱）" }
  ]
}
```

- `severity`：`block`（exit 2 阻断）| `warn`（限频提示）
- `pattern` 与 `script` 二选一；`pattern` 逐行匹配
- 脚本约定：`node <script> <filePath>` 运行（相对规则集目录），退出码 0=通过、
  非 0=违规（stdout 即违规说明）；脚本只能位于包目录内
- 每条规则的 `message` 必须写清**修复路径**——agent 靠它自修

## 校验与贡献

```bash
# 本地自检（CI 对 domains/ 下所有包执行同一校验）
python scripts/validate-domain-pack.py domains/<name>

# 从模板生成新包骨架（在希望创建的位置的父目录执行）
python scripts/create-domain-pack.py <name>
```

贡献流程见仓库根 CONTRIBUTING.md「贡献领域包」：基于 `_template` 脚手架、
校验通过、附至少 1 个评测示例（规则命中/放行各一）、提 PR。

## 版本化与演进

- 运行时破坏性变更（规则集 schema / 配置字段变更）→ 提升 `schemaVersion`，
  并同步更新本规范与 `validate-domain-pack.py`
- 领域包自身规则演进只改自己的 `version`；规则删除/收紧视为 minor 变更并在
  包 README 记录影响
