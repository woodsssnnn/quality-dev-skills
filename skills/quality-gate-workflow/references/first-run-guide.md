# QGW 首次使用引导

> 本文档在用户首次使用 QGW 时自动展示，帮助快速选择正确的工作流。

## 触发条件

当同时满足以下条件时，Agent 应展示本引导：
- `.qgw/` 目录不存在（首次使用）或 `.qgw/sessions/` 为空
- 用户消息不含任何 QGW 参数（`--gate1`/`--gate2`/`--all`/`--self`/`--analyze`/`--preset`/`--auto`）
- 当前会话未执行过任何 Gate 流程

## 引导内容

展示以下引导信息：

```
🚀 欢迎使用质量门禁工作流（QGW）！

根据你的需要选择：

1️⃣ 我有需求文档/PRD → 我会帮你制定开发计划
   用法：粘贴 PRD 内容，或直接说"帮我规划这个需求"
   等价参数：--gate1 --prd

2️⃣ 我已有开发计划，想实现代码 → 我会按计划写代码并验证
   用法：--gate2 或指定 plan 文件路径
   等价参数：--gate2 --impl

3️⃣ 我想快速修个 Bug → 直接定位并修复
   用法：--preset quickfix 或描述 Bug 现象
   等价参数：--gate2 --debug

4️⃣ 我想做完整功能开发 → 从需求到代码全流程
   用法：--preset feature 或 --all
   等价参数：--all --strict

5️⃣ 我想审计已有代码 → 检查代码与计划的一致性
   用法：--preset audit
   等价参数：--gate2 --audit

6️⃣ 我想了解高级用法 → 查看所有参数和定制选项
   用法：--help 或查看 SKILL.md 的"全部参数"章节
```

## 智能推断规则详解

当用户未指定参数时，QGW 按以下规则推断：

### 规则优先级

| 优先级 | 输入特征 | 推断结果 | 说明 |
|--------|---------|----------|------|
| 1 | 含已有 Plan 文件路径 | `--gate2 --impl` | 路径匹配 `*/plan/*` 或 `*/plans/*` |
| 2 | `.qgw/sessions/` 有活跃记录 | 提示恢复上次会话 | 列出未完成 session 供选择 |
| 3 | 含错误日志/堆栈/异常信息 | `--gate2 --debug` | 出现 stack trace 或错误码 |
| 4 | 含 Bug 描述（无堆栈） | `--gate1 --bug` 或 `--gate2 --debug` | 需进一步判断是否需要 Plan |
| 5 | 含 PRD/需求文档 | `--gate1 --prd` | 出现"需求""功能描述"等 |
| 6 | 含"重构""优化" | `--gate1 --opt` | 语义匹配 |
| 7 | 含"审计""检查代码" | `--gate2 --audit` | 语义匹配 |
| 8 | 无法匹配 | 展示本引导 | 让用户手动选择 |

### Bug 模式 vs Debug 模式的判断

- **需要 Plan（`--gate1 --bug`）**：Bug 涉及多文件/多模块、需要分析根因、修复方案不确定
- **不需要 Plan（`--gate2 --debug`）**：Bug 定位明确、单文件修复、错误信息直接指向问题

### 推断输出格式

```
💡 建议参数：--gate1 --prd
   原因：检测到需求文档内容
   预设替代：--preset feature（如需完整流程）

确认后开始执行，或告诉我你想要的参数。
```

### 多规则匹配

当多个规则同时匹配时：

```
💡 检测到多种可能的意图：

1. 需求规划（--gate1 --prd）— 因为检测到需求文档
2. Bug 修复（--gate2 --debug）— 因为检测到错误描述

请选择一个，或告诉我你具体想做什么。
```

## 项目初始化引导

当用户首次使用且 `.qgw/` 不存在时，建议使用 `qgw-init` 技能进行初始化：

```
📁 提示：当前项目尚未初始化 QGW 工作区。

推荐：说“初始化 QGW”或使用 --init 参数，启动交互式引导。
也可以使用脚本快速初始化：bash skills/qgw-init/scripts/qgw-init.sh --yes

QGW 可以在无 .qgw/ 的情况下正常运行，但项目定制（constitution、模板覆盖等）需要此目录。
```

详细初始化流程 → [qgw-init SKILL.md](../../qgw-init/SKILL.md)

## 快速参考

| 我想... | 最简单的方式 | 完整参数 |
|---------|-------------|---------|
| 规划一个新需求 | 粘贴 PRD 内容 | `--gate1 --prd` |
| 按已有 Plan 写代码 | `--gate2` + Plan 路径 | `--gate2 --impl` |
| 快速修 Bug | 描述 Bug 现象 | `--gate2 --debug` |
| 完整开发一个功能 | `--preset feature` | `--all --strict` |
| 紧急修复 | `--preset hotfix` | `--gate1 --bug` → `--gate2 --debug` |
| 复盘会话质量 | `--preset review` | `--self` |
| 审计代码 | `--preset audit` | `--gate2 --audit` |
| 轻量改动 | `--preset minimal` | `--gate1 --lite` → `--gate2 --incremental` |
