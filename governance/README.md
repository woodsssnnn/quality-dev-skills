# governance — 通用代码治理运行时

governance 是本仓库的**代码级门禁运行时**：在 agent 每次写文件、跑命令、
提交 prompt、结束回复的时点上，执行声明式规则校验、留下机器可查的事件
凭证。它与 `skills/quality-gate-workflow`（流程级门禁：PRD→Plan→Verifier）
互补，共同构成本仓库的治理体系。

核心特征：**零领域假设**——所有领域相关的规则、关键词、提示全部外置为
数据文件（三层发现），运行时本身只提供机制。

## 架构

```
PostToolUse(Edit|Write|Bash|Read) ─→ run-checks.js ─┬─ Edit/Write: 规则引擎（block→exit 2 阻断）
                                                    ├─ Bash: 验证运行审计（DoD 机器凭证）+ 命令提示
                                                    └─ Read: 轻量记录
UserPromptSubmit ─────────────────→ prompt-inject.js   语境提示注入（配置驱动，默认空=零噪音）
Stop ────────────────────────────→ turn-stats.js      每轮统计（仅 stderr，防 Stop 死循环）
SessionStart ────────────────────→ integrity-check.js 判题机自保护（安装快照比对 + --self-test）
                                                        │
                                        全部事件 append-only 写入事件流（SHA-256 哈希链）
                                        ~/.zcode/governance-data/governance-events.jsonl
```

## 目录

```
governance/
├── config.default.json     # 内置默认配置（全部空/中立值）
├── hooks/                  # 4 个 hook 入口 + Windows .cmd 包装 + lib/
│   ├── hooks.json          # hook 注册模板（插件打包用 ${CLAUDE_PLUGIN_ROOT}）
│   └── lib/                # hook-input / config / rules / hint-state / data-home / integrity
├── rules/builtin/          # 内置中立规则集（密钥泄漏、调试残留）
├── scripts/
│   ├── event-log.js        # 事件流 append（哈希链）
│   ├── event-query.js      # 事件流查询（--tail/--chain-verify/--verify-last/--freq）
│   ├── verify-links.js     # md 内链校验（CI / 单文件，断链 exit 1）
│   └── blast-radius.js     # 符号影响面分析（def/call/ref 分类 + 同义符号线索）
└── tests/run-tests.js      # 自测（node governance/tests/run-tests.js）
```

## 配置发现（三层，高优先级覆盖低优先级）

1. **内置默认** `governance/config.default.json`
2. **领域包** 项目声明的 packs（见下）各自的 `governance.json`
3. **项目本地** `<projectDir>/.qgw/governance.json`

项目根目录来自 `ZCODE_PROJECT_DIR` / `CLAUDE_PROJECT_DIR` 环境变量（hook
进程注入），兜底 stdin 的 `cwd`。

配置字段（列表类逐层拼接，其余字段高优先级覆盖）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `packs` | string[] | 声明启用的领域包名（仅项目层有意义） |
| `promptMessages` | {id?, pattern, flags?, message, cap?}[] | UserPromptSubmit 提示注入规则 |
| `verifyCommands` | {name, commandPattern, passPattern?, failPattern?}[] | 本地验证命令识别模式（验证审计用） |
| `bashHints` | {id?, pattern, message, cap?}[] | Bash 命令提示（非阻断，限频） |
| `hints` | {id, message, extensions?, filenamePattern?, cap?}[] | 文件编辑提示（非阻断，限频） |
| `projectMarkers` | {files, content} | 项目识别标记（领域包/项目自定义） |

## 规则集（声明式门禁）

发现顺序（同 id 规则集后者覆盖前者）：

1. `governance/rules/builtin/*.json` — 内置中立规则
2. `<packDir>/rules/*.json` — 领域包规则
3. `<projectDir>/.qgw/rules/*.json` — 项目本地规则（最高优先）

规则集 schema：

```json
{
  "id": "my-rules",
  "version": "1.0.0",
  "description": "说明",
  "appliesTo": { "extensions": [".ts", ".java"] },
  "rules": [
    {
      "id": "R-001",
      "severity": "block",              // block=exit 2 阻断；warn=提示（限频）
      "pattern": "\\bforbiddenApi\\(",  // JS 正则，逐行匹配
      "flags": "i",
      "message": "为什么禁止、应该怎么改"
    },
    {
      "id": "R-002",
      "severity": "block",
      "script": "check-complex.js",     // 脚本逃生舱：node <script> <file>，非 0 即违规
      "message": "复杂度超标"
    }
  ]
}
```

### 领域包（domain pack）

领域包是一个目录，让某个技术栈/团队的规则接入运行时：

```
my-pack/
├── governance.json    # 该包的配置增量（promptMessages/verifyCommands/...）
└── rules/*.json       # 该包的规则集
```

启用方式：项目 `.qgw/governance.json` 声明 `"packs": ["my-pack"]`。解析
位置：`<projectDir>/.qgw/packs/my-pack/`（项目私有）优先，其次本仓库
`domains/my-pack/`（社区贡献，见仓库根 CONTRIBUTING.md）。

## 事件流（自进化数据底座）

- 路径：`~/.zcode/governance-data/governance-events.jsonl`（`GOVERNANCE_DATA_HOME` 可覆盖）
- append-only，每条带 `prev` = 前一条原始行的 SHA-256（哈希链，篡改可见）
- 事件类型：`gate`（逐违规）/ `summary`（逐文件汇总）/ `verify`（验证凭证）/
  `hint`（提示曝光）/ `integrity` / `turn-start` / `turn-summary` / `insight`
- 测试夹具路径（`__test__/`、`(test|spec)/fixtures/`）不写入生产事件流

查询：`node governance/scripts/event-query.js --tail 20 | --chain-verify | --verify-last | --freq`

### verify 机器凭证（DoD 审计链）

"agent 声称验证过"与"验证真的跑过"是两回事。当 agent 经 Bash 工具运行
配置识别的验证命令时，run-checks 从工具回包解析结论行并与 exitCode 交叉
核验，落一条 `verify` 事件（带 session）。评审者用 `--verify-last` 核对
凭证，防止"没跑却说跑了"。

## 完整性自保护（判题机）

`integrity-check.js --write-anchor` 在安装时对运行时目录做 CRLF 归一快照；
每会话启动时比对当前树与快照，drift 即告警（stderr + additionalContext）。
`--self-test` 用临时目录验证检测器本身（judging the judge）。

## hook 协议要点（贡献者必读）

- **退出码**：PostToolUse `0`=放行、`2`=阻断（stderr 喂回 agent）；其余
  hook 永远 `0`
- **自身异常永不阻断 agent**：所有内部失败 catch 后放行，仅留 stderr 信号
- **stdin 双格式归一**：信封字段 snake_case/camelCase 均可（lib/hook-input.js）
- **Stop hook 只写 stderr**：stdout 会触发 agent 继续形成死循环
- **提示必须限频**：同 (kind,key) 每会话一次 + 会话封顶（lib/hint-state.js）
- **Windows**：`.cmd` 包装用 `%~dp0` 定位脚本；hooks.json 中 command 不加引号

## 自测

```bash
node governance/tests/run-tests.js          # 全部模块
node governance/hooks/integrity-check.js --self-test
node governance/scripts/event-query.js --chain-verify
```
