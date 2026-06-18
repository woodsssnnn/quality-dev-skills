# 测试用例模板

用于生成技能优化的测试用例。

## 格式

```markdown
### Test Case: [名称]

**用户输入**: [用户会说什么]

**期望行为**: [agent 应该做什么]

**期望输出**: [输出格式或内容]

**验证规则**: [用哪些 scoring-rules 验证]
```

## 示例

### Test Case: 触发技能

**用户输入**: "优化 quality-gate-workflow 技能"

**期望行为**: 
1. 识别 skill-optimizer 技能
2. 读取目标技能文件
3. 开始评估流程

**期望输出**: 
- 技能结构摘要
- 基线分数

**验证规则**: description_trigger, has_checklist

---

### Test Case: 评分

**用户输入**: "评估这个技能的质量"

**期望行为**: 
1. 加载 scoring-rules
2. 对技能运行 9 条检查
3. 计算总分

**期望输出**: 
- JSON 格式的评估结果
- 每条规则的 pass/fail 状态

**验证规则**: clear_gates, has_progress_output

---

### Test Case: 优化循环

**用户输入**: "开始优化循环"

**期望行为**: 
1. 生成 test cases
2. 运行 rollout
3. 分析失败
4. 生成 edit 候选
5. 应用 bounded edit
6. 在 val set 上验证

**期望输出**: 
- 每轮 score 对比
- 优化后的技能文件

**验证规则**: no_anti_patterns, reference_depth
