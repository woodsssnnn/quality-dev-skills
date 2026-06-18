# 优化算法

SkillOpt 方法论的完整伪代码实现。

## 核心循环

### 主循环：优化目标技能

```python
def optimize_skill(target_skill_path: str, config: dict):
    """
    优化技能质量的主循环。
    
    Args:
        target_skill_path: 目标技能路径
        config: 配置参数 (max_epochs, train_ratio, output_dir)
    
    Returns:
        optimized_skill_path, final_score
    """
    # Step 1: 加载技能
    skill = load_skill(target_skill_path)
    
    # Step 2: 生成 test cases
    train_cases, val_cases = generate_test_cases(skill, config['train_ratio'])
    
    # Step 3: 基线测试
    baseline_score = evaluate(skill, train_cases + val_cases)
    print(f"Baseline score: {baseline_score:.3f}")
    
    # Step 4: 优化循环
    best_skill = skill
    best_score = baseline_score
    
    for epoch in range(config['max_epochs']):
        print(f"\n--- Epoch {epoch + 1} ---")
        
        # a. Rollout: 用当前 skill 执行 train cases
        train_results = rollout(best_skill, train_cases)
        
        # b. 找到失败点
        failures = [r for r in train_results if r.score < THRESHOLD]
        if not failures:
            print("No failures found, stopping early")
            break
        
        # c. Reflect: 让 LLM 分析失败并生成 edit 候选
        edit_candidates = reflect(best_skill, failures)
        
        # d. 逐个尝试 edit
        improved = False
        for edit in edit_candidates:
            candidate = apply_bounded_edit(best_skill, edit)
            
            # e. Gate: 在 val cases 上验证
            val_score = evaluate(candidate, val_cases)
            
            # f. 如果 val_score > baseline → 接受
            if val_score > best_score:
                best_skill = candidate
                best_score = val_score
                print(f"Accepted edit: {edit.description}, score {val_score:.3f}")
                improved = True
                break
        
        if not improved:
            print(f"No edit improved score, stopping at epoch {epoch + 1}")
            break
    
    # Step 5: 最终验证
    final_score = evaluate(best_skill, train_cases + val_cases)
    print(f"\nFinal score: {final_score:.3f} (baseline: {baseline_score:.3f})")
    
    # Step 6: 输出
    save_optimized(best_skill, config['output_dir'])
    generate_report(epoch + 1, baseline_score, final_score, config['output_dir'])
    
    return best_skill, final_score
```

### 元循环：优化评估规则本身

```python
def optimize_evaluator(target_skill_path: str, config: dict):
    """
    优化评估规则本身的元循环。
    
    当评估结果有假阳性（规则过于严格）或假阴性（规则遗漏）时，
    自动调整评分规则。
    
    Args:
        target_skill_path: 目标技能路径（用于验证规则调整）
        config: 配置参数
    
    Returns:
        optimized_rules, report
    """
    # Step 1: 初始评估
    skill = load_skill(target_skill_path)
    initial_result = evaluate(skill)
    
    print(f"Initial score: {initial_result['total_score']:.3f}")
    print(f"Failed rules: {[c['rule'] for c in initial_result['checks'] if not c['passed']]}")
    
    # Step 2: 分析假阳性/假阴性
    false_positives = identify_false_positives(initial_result)
    false_negatives = identify_false_negatives(initial_result)
    
    if not false_positives and not false_negatives:
        print("No rule adjustments needed")
        return get_current_rules(), None
    
    # Step 3: 调整规则
    adjusted_rules = adjust_rules(false_positives, false_negatives)
    
    # Step 4: 验证调整后的规则
    optimized_result = evaluate_with_rules(skill, adjusted_rules)
    
    print(f"Optimized score: {optimized_result['total_score']:.3f}")
    
    # Step 5: 输出报告
    report = {
        'initial_score': initial_result['total_score'],
        'optimized_score': optimized_result['total_score'],
        'false_positives': false_positives,
        'false_negatives': false_negatives,
        'rule_changes': get_rule_changes(adjusted_rules),
    }
    
    save_evaluator_report(report, config['output_dir'])
    
    return adjusted_rules, report


def identify_false_positives(result: dict) -> list:
    """
    识别假阳性：规则判定失败，但实际是合法的。
    
    常见假阳性：
    1. reference_depth: skill 内部引用被误判为深层引用
    2. no_anti_patterns: 文档性日期被误判为时效性日期
    3. no_anti_patterns: 规则编号被误判为魔法数字
    """
    false_positives = []
    
    for check in result['checks']:
        if not check['passed']:
            # 分析是否为假阳性
            if check['rule'] == 'reference_depth':
                # 检查是否都是内部引用
                if is_all_internal_refs(check['detail']):
                    false_positives.append({
                        'rule': check['rule'],
                        'reason': 'All deep references are internal skill references',
                    })
            
            elif check['rule'] == 'no_anti_patterns':
                # 检查日期是否为文档性
                if is_documentation_dates(check['detail']):
                    false_positives.append({
                        'rule': check['rule'],
                        'reason': 'Dates are documentation timestamps, not temporal deadlines',
                    })
    
    return false_positives


def identify_false_negatives(result: dict) -> list:
    """
    识别假阴性：规则判定通过，但实际有问题。
    
    常见假阴性：
    1. has_progress_output: 步骤没有明确的输入/输出
    2. clear_gates: 没有量化的 pass/fail 标准
    """
    false_negatives = []
    
    for check in result['checks']:
        if check['passed']:
            # 分析是否为假阴性
            if check['rule'] == 'has_progress_output':
                if lacks_explicit_io(check['detail']):
                    false_negatives.append({
                        'rule': check['rule'],
                        'reason': 'Steps lack explicit input/output format',
                    })
    
    return false_negatives


def adjust_rules(false_positives: list, false_negatives: list) -> dict:
    """
    根据假阳性/假阴性调整规则。
    """
    rules = get_current_rules().copy()
    
    # 处理假阳性：放宽规则
    for fp in false_positives:
        rule_id = fp['rule']
        if rule_id == 'reference_depth':
            # 排除内部引用
            rules[rule_id]['exclude_internal'] = True
        elif rule_id == 'no_anti_patterns':
            # 区分文档性日期和时效性日期
            rules[rule_id]['allow_documentation_dates'] = True
            rules[rule_id]['allow_rule_numbers'] = True
    
    # 处理假阴性：收紧规则
    for fn in false_negatives:
        rule_id = fn['rule']
        if rule_id == 'has_progress_output':
            # 要求明确的输入/输出格式
            rules[rule_id]['require_explicit_io'] = True
    
    return rules
```

## 子流程

### Rollout

```python
def rollout(skill, test_cases):
    """
    用 subagent 在 test cases 上执行技能。
    
    对每个 test case:
    1. 清空上下文
    2. 给 subagent 注入 skill 内容
    3. 发送 user_input
    4. 记录 agent 的行为轨迹
    5. 用 scoring-rules 评估行为
    """
    results = []
    for case in test_cases:
        # 注入 skill
        context = f"你是一个 AI 助手。以下是你要使用的技能:\n\n{skill.content}\n\n"
        
        # 执行
        agent = spawn_subagent(context + case.user_input)
        trajectory = agent.run()
        
        # 评分
        score = score_trajectory(trajectory, case.expected_behavior)
        
        results.append({
            'case': case,
            'trajectory': trajectory,
            'score': score
        })
    
    return results
```

### Reflect

```python
def reflect(skill, failures):
    """
    分析失败轨迹，生成 edit 候选。
    
    对每个失败:
    1. 分析 agent 的行为轨迹
    2. 找到违规点
    3. 生成修改建议
    """
    edit_candidates = []
    
    for failure in failures:
        # 让 LLM 分析
        prompt = f"""
        技能内容:
        {skill.content}
        
        失败轨迹:
        {failure.trajectory}
        
        违规规则: {failure.violated_rules}
        
        请分析失败原因，并生成一个修改建议来修复这个问题。
        修改建议必须是 bounded edit（只改文本，不改结构）。
        """
        
        edit = llm_call(prompt)
        edit_candidates.append(edit)
    
    return edit_candidates
```

### Apply Bounded Edit

```python
def apply_bounded_edit(skill, edit):
    """
    应用 bounded edit。
    
    约束:
    1. 只修改文本内容
    2. 不改文件名
    3. 不增删文件
    4. 不改目录结构
    """
    new_content = skill.content
    
    # 应用编辑
    for change in edit.changes:
        new_content = new_content.replace(change.old, change.new)
    
    return Skill(content=new_content)
```

## 配置参数

```yaml
# 默认配置
max_epochs: 5          # 最大优化轮数
train_ratio: 0.8       # 训练集比例
score_threshold: 0.7   # 及格线
output_dir: ./optimized
```
