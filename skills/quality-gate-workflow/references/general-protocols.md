# 通用工作协议

> 本文件从 gate1-workflow.md 抽离，适用于 Gate 1、Gate 2、Debug、Audit 所有工作流。

## 5问题重启测试

借鉴 planning-with-files，会话恢复时必须通过5问题测试：

| 问题 | 答案来源 | 验证方式 |
|------|----------|----------|
| **我在哪？** | 当前阶段 | `docs/QGW-INDEX.md` Active Sessions |
| **我要去哪？** | 剩余阶段 | Plan文档的Phase列表 |
| **目标是什么？** | 需求目标 | Plan文档的Goal声明 |
| **学到了什么？** | 发现和决策 | `docs/verification/*.json` |
| **做了什么？** | 执行记录 | `docs/sessions/*.md` |

**执行时机**：
- 会话启动时（on-session-start hook）
- /clear 恢复后
- context compaction 后
- 长时间暂停后恢复

**验证失败处理**：
- 无法回答任一问题 → 输出 `[qgw] ⚠️ 会话状态不完整，需要重新加载`
- 自动尝试从文件恢复
- 恢复失败 → 提示用户手动恢复

> 引擎 `resume` 命令会自动执行此测试并输出结构化 JSON。

## 2-Action Rule

借鉴 planning-with-files，每2次view/search操作后必须更新文件：

```markdown
操作1: Grep搜索 → 记录发现
操作2: Read文件 → 必须更新 findings
操作3: Glob搜索 → 记录发现
操作4: Grep搜索 → 必须更新 findings
```

**适用场景**：
- P1.5 数据库调查
- P1.6 代码链路调查
- Gate 2 代码实现

**执行方式**：
- 每2次操作后自动提醒
- 更新对应的verification JSON或session summary
- 防止信息丢失

## 3-Strike Error Protocol

借鉴 planning-with-files，错误处理必须遵循3次尝试协议：

```markdown
尝试1: 诊断并修复
  → 仔细阅读错误信息
  → 识别根因
  → 应用针对性修复

尝试2: 替代方法
  → 相同错误？尝试不同方法
  → 不同工具？不同库？
  → 绝不重复完全相同的操作

尝试3: 重新思考
  → 质疑假设
  → 搜索解决方案
  → 考虑更新计划

3次失败后: 升级给用户
  → 解释尝试了什么
  → 分享具体错误
  → 请求指导
```

**执行规则**：
- 错误必须记录到Plan文档的Errors Encountered表
- 每次尝试必须记录到progress.md
- 3次失败后必须停止并报告用户
- 禁止静默跳过错误
