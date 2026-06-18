# Qoder CLI 工具映射

本技能使用 Claude Code 工具名作为基准语言。在 Qoder CLI 中运行时，按以下映射使用对应工具。

## 工具对应表

| Claude Code（基准） | Qoder CLI | 说明 |
|---|---|---|
| `Task` | `Agent` | 派发子代理；Qoder 无 `Task` 工具 |
| `Agent` | `Agent` | 名称相同；注意 `subagent_type` 参数 |
| `Read` | `Read` | 完全一致 |
| `Grep` | `Grep` | 完全一致 |
| `Glob` | `Glob` | 完全一致 |
| `Bash` | `Bash` | 完全一致 |
| `Write` | `Write` | 完全一致 |

## 关键差异：Task → Agent

Claude Code 的 `Task` 工具在 Qoder 中不存在，统一使用 `Agent` 工具替代。

### Agent 工具参数

```
Agent({
  description: "简短任务描述",
  prompt: "子代理的完整指令",
  subagent_type: "general-purpose"   // 可选，见下表
})
```

### subagent_type 选型

| 场景 | subagent_type | 说明 |
|---|---|---|
| 代码库探索、文件搜索 | `Explore` | 快速只读探索，不做修改 |
| 通用研究、多步骤任务 | `general-purpose`（默认） | 全工具访问，适合 verifier 子代理 |
| 前端架构分析 | `frontend-architect` | 只读分析，不写代码 |
| 后端架构分析 | `backend-architect` | 只读分析，不写代码 |

### 本技能中的具体用法

| 技能步骤 | Claude Code 写法 | Qoder CLI 写法 |
|---|---|---|
| Gate 1 P4 verifier | `Task({ description: "plan verifier", prompt: "..." })` | `Agent({ description: "plan verifier", prompt: "...", subagent_type: "general-purpose" })` |
| Gate 2 S4 verifier | `Task({ description: "code verifier", prompt: "..." })` | `Agent({ description: "code verifier", prompt: "...", subagent_type: "general-purpose" })` |
| Audit verifier | `Task({ description: "audit verifier", prompt: "..." })` | `Agent({ description: "audit verifier", prompt: "...", subagent_type: "general-purpose" })` |
| Debug verifier | `Task({ description: "debug verifier", prompt: "..." })` | `Agent({ description: "debug verifier", prompt: "...", subagent_type: "general-purpose" })` |

## 派发子代理时的注意事项

1. **Qoder 的 `Agent` 工具不支持 `subagent_type: "verifier"`**：用 `"general-purpose"` 代替，在 `prompt` 中明确说明 verifier 角色
2. **prompt 必须自包含**：子代理无法访问主会话上下文，所有必要信息（验收标准、文件路径、验证规则）必须写入 prompt
3. **toolCallId 获取**：Qoder 的 Agent 工具返回结果中无 `toolCallId` 字段，用子代理返回的文本摘要作为验证证据记录到验收 JSON
