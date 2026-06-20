# 智能推断规则（`--auto` 模式）

> 本文档由 SKILL.md 路由自动加载（零参数推断时）。

当用户消息不含显式参数时，QGW 根据输入内容自动推断：

| 输入特征 | 推断结果 | 置信度信号 |
|---------|----------|------------|
| 含 PRD/需求文档文本或路径 | `--gate1 --prd` | 出现"需求""PRD""功能描述"等关键词 |
| 含 Bug 描述/错误日志/堆栈 | `--gate2 --debug`（无 Plan）或 `--gate1 --bug`（需 Plan） | 出现"错误""Bug""异常""500"等关键词 |
| 含已有 Plan 文件路径 | `--gate2 --impl` | 路径指向 plan/ 目录下的 .md 文件 |
| 含"重构""优化""改进" | `--gate1 --opt` | 语义匹配 |
| `.qgw/sessions/` 有活跃记录 | 提示恢复上次会话 | 检测到未完成 session |
| 含"审计""检查已有代码" | `--gate2 --audit` | 语义匹配 |

## 推断流程

1. 分析用户输入，匹配上表规则
2. 输出建议：`💡 建议参数：--gate1 --prd（原因：检测到需求文档内容）`
3. 等待用户确认或调整
4. 确认后按推断参数执行

## 多规则匹配处理

多个规则匹配时，列出所有候选让用户选择。无法匹配时展示 [first-run-guide](first-run-guide.md) 引导。

## 推断决策树

```
用户输入
├─ 含 PRD 文档或需求描述 → --gate1 --prd
├─ 含 Bug/错误描述
│   ├─ 已有 Plan → --gate2 --debug
│   └─ 无 Plan → --gate1 --bug
├─ 含 Plan 文件路径 → --gate2 --impl
├─ 含重构/优化意图 → --gate1 --opt
├─ 含“PRD 改了”“需求变了” → --prd-changed + 推断 impact
├─ 含“上次做到一半”“继续” → resume
├─ 含“学到了”“反模式” → evolve（自动触发，无需显式参数）
├─ 含“Plan 有问题” → 建议重新 gate1
├─ 有活跃 session → 提示 resume
├─ 含审计/检查意图 → --gate2 --audit
└─ 无法匹配 → 展示 first-run-guide
```

## Preset 预设展开

| Preset | 展开参数 | 适用场景 |
|--------|---------|---------|
| `quickfix` | `--gate2 --debug` | 快速修 Bug |
| `feature` | `--all --strict` | 完整功能开发 |
| `hotfix` | `--gate1 --bug → --gate2 --debug` | 紧急修复全链路 |
| `review` | `--self` | 复盘最近会话 |
| `audit` | `--gate2 --audit` | 审计已有代码 |
| `minimal` | `--gate1 --lite → --gate2 --incremental` | 轻量快速通道 |

> Preset 只是参数别名，展开后仍走完整 Gate 流程，**不绕过任何门禁**。
