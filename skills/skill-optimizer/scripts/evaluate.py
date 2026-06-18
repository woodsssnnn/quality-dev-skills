#!/usr/bin/env python3
"""
evaluate.py - 技能质量评估器

用法: python evaluate.py <skill-path>

输出: JSON 格式的评估结果
"""

import sys
import os
import re
import json
from pathlib import Path


# 评分规则定义
RULES = [
    {
        "id": "description_trigger",
        "check": "description starts with 'Use when'",
        "weight": 0.15,
        "auto_fix": True,
    },
    {
        "id": "no_workflow_in_desc",
        "check": "description does not contain workflow steps",
        "weight": 0.15,
        "auto_fix": True,
    },
    {
        "id": "token_efficiency",
        "check": "SKILL.md lines < 500",
        "weight": 0.10,
        "auto_fix": False,
    },
    {
        "id": "reference_depth",
        "check": "file references are one level deep",
        "weight": 0.10,
        "auto_fix": False,
    },
    {
        "id": "no_anti_patterns",
        "check": "no temporal info, no magic numbers, no nested refs",
        "weight": 0.15,
        "auto_fix": False,
    },
    {
        "id": "has_checklist",
        "check": "workflow has checklist or numbered steps",
        "weight": 0.10,
        "auto_fix": False,
    },
    {
        "id": "has_progress_output",
        "check": "steps have entry/exit logging",
        "weight": 0.10,
        "auto_fix": False,
    },
    {
        "id": "rationalization_table",
        "check": "has anti-pattern rebuttal table",
        "weight": 0.10,
        "auto_fix": False,
    },
    {
        "id": "clear_gates",
        "check": "pass/fail criteria are explicit",
        "weight": 0.05,
        "auto_fix": False,
    },
]


def load_skill(skill_path: str) -> dict:
    """加载技能文件"""
    skill_dir = Path(skill_path)
    skill_md = skill_dir / "SKILL.md"
    
    if not skill_md.exists():
        raise FileNotFoundError(f"SKILL.md not found at {skill_md}")
    
    content = skill_md.read_text(encoding="utf-8")
    
    # 提取 frontmatter
    frontmatter = {}
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            fm_text = content[3:end].strip()
            lines = fm_text.split("\n")
            i = 0
            while i < len(lines):
                line = lines[i]
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    # 处理 YAML block scalar (|- or >-)
                    if value in ["|-", ">-"]:
                        # 收集缩进的后续行
                        block_lines = []
                        i += 1
                        while i < len(lines) and (lines[i].startswith("  ") or lines[i].startswith("\t")):
                            block_lines.append(lines[i].strip())
                            i += 1
                        frontmatter[key] = "\n".join(block_lines)
                        continue
                    # 去除引号包裹
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    frontmatter[key] = value
                i += 1
    
    # 检查 references 目录
    references_dir = skill_dir / "references"
    references = []
    if references_dir.exists():
        references = [f.name for f in references_dir.iterdir() if f.is_file()]
    
    return {
        "path": str(skill_dir),
        "content": content,
        "frontmatter": frontmatter,
        "references": references,
        "line_count": len(content.split("\n")),
    }


def check_description_trigger(skill: dict) -> dict:
    """检查 description 是否以 'Use when' 开头"""
    desc = skill["frontmatter"].get("description", "")
    passed = desc.startswith("Use when")
    return {
        "rule": "description_trigger",
        "passed": passed,
        "detail": f"description starts with: {desc[:30]}...",
    }


def check_no_workflow_in_desc(skill: dict) -> dict:
    """检查 description 不包含工作流步骤"""
    desc = skill["frontmatter"].get("description", "")
    workflow_keywords = ["Step 1", "步骤", "流程", "Phase"]
    has_workflow = any(kw in desc for kw in workflow_keywords)
    passed = not has_workflow
    return {
        "rule": "no_workflow_in_desc",
        "passed": passed,
        "detail": f"workflow keywords found: {[kw for kw in workflow_keywords if kw in desc]}",
    }


def check_token_efficiency(skill: dict) -> dict:
    """检查 SKILL.md 行数 < 500"""
    passed = skill["line_count"] < 500
    return {
        "rule": "token_efficiency",
        "passed": passed,
        "detail": f"line count: {skill['line_count']}",
    }


def check_reference_depth(skill: dict) -> dict:
    """检查引用文件只有一层深（排除 skill 内部引用和目录引用）"""
    content = skill["content"]
    skill_path = Path(skill["path"])
    
    # 查找 markdown 引用
    refs = re.findall(r'\[.*?\]\((.*?)\)', content)
    
    deep_refs = []
    for r in refs:
        # 排除 http 链接
        if r.startswith("http"):
            continue
        # 排除目录引用（以 / 结尾）
        if r.endswith("/"):
            continue
        # 排除 scripts/ 引用（验证脚本）
        if r.startswith("./scripts/"):
            continue
        # 排除 skill 内部 references/ 引用（如 ./references/frontend/rules/xxx.md）
        if r.startswith("./references/") or r.startswith("references/"):
            continue
        # 排除 ../ 引用（跨技能引用）
        if r.startswith("../"):
            continue
        # 其他引用检查深度
        if r.count("/") > 1:
            deep_refs.append(r)
    
    passed = len(deep_refs) == 0
    return {
        "rule": "reference_depth",
        "passed": passed,
        "detail": f"deep references found: {len(deep_refs)}" if deep_refs else "no deep references",
    }


def check_no_anti_patterns(skill: dict) -> dict:
    """检查无时间信息、魔法数字、嵌套引用"""
    content = skill["content"]
    issues = []
    
    # 检查时间信息（YYYY-MM-DD 格式，但排除变更日志和脚本验证时间戳）
    # 时效性日期：出现在句子中，如 "截至 2026-06-15"
    # 文档性日期：出现在括号或脚本中，如 "v2.3（2026-06-11）" 或 "verifiedDate: '2026-06-11'"
    temporal_pattern = r'(?:截至|截止|有效期|过期|deadlin)[^)\n]*\d{4}[-/]\d{1,2}[-/]\d{1,2}'
    if re.search(temporal_pattern, content):
        issues.append("temporal deadline found")
    
    # 检查魔法数字（排除规则编号、版本号、行号等）
    # 规则编号：两位数字如 00, 01, 12
    # 版本号：如 4.24.8, 5.2.0
    # 独立出现的数字才可能是魔法数字
    magic_pattern = r'(?<!\d)(?<![/\\.#])\d{3,}(?!\d)(?![/\\.#])'
    magic_matches = re.findall(magic_pattern, content)
    # 过滤掉合理的数字（端口号、HTTP 状态码、大数字等）
    reasonable = {'100', '299', '5476951', '68006', '2375', '8080', '3000', '8072',
                  '401', '404', '500', '502', '503', '504', '200', '301', '302'}
    filtered = [m for m in magic_matches if m not in reasonable]
    if len(filtered) > 5:
        issues.append(f"magic numbers found: {len(filtered)}")
    
    passed = len(issues) == 0
    return {
        "rule": "no_anti_patterns",
        "passed": passed,
        "detail": f"issues: {issues}" if issues else "no issues",
    }


def check_has_checklist(skill: dict) -> dict:
    """检查工作流有检查清单或编号步骤"""
    content = skill["content"]
    has_numbered = bool(re.search(r'^\d+\.\s', content, re.MULTILINE))
    has_checklist = bool(re.search(r'^- \[ \]', content, re.MULTILINE))
    passed = has_numbered or has_checklist
    return {
        "rule": "has_checklist",
        "passed": passed,
        "detail": f"numbered: {has_numbered}, checklist: {has_checklist}",
    }


def check_has_progress_output(skill: dict) -> dict:
    """检查步骤有入口/出口日志"""
    content = skill["content"]
    output_keywords = ["输出", "输出:", "output:", "Output:", "产出"]
    has_output = any(kw in content for kw in output_keywords)
    return {
        "rule": "has_progress_output",
        "passed": has_output,
        "detail": f"output keywords found: {[kw for kw in output_keywords if kw in content]}",
    }


def check_rationalization_table(skill: dict) -> dict:
    """检查有反模式反驳表"""
    content = skill["content"]
    # 查找 markdown 表格
    tables = re.findall(r'\|.*\|.*\|', content)
    has_table = len(tables) > 0
    return {
        "rule": "rationalization_table",
        "passed": has_table,
        "detail": f"tables found: {len(tables)}",
    }


def check_clear_gates(skill: dict) -> dict:
    """检查 pass/fail 标准明确"""
    content = skill["content"]
    gate_keywords = ["通过条件", "失败条件", "pass", "fail", "通过", "失败"]
    has_gates = any(kw in content.lower() for kw in gate_keywords)
    return {
        "rule": "clear_gates",
        "passed": has_gates,
        "detail": f"gate keywords found: {[kw for kw in gate_keywords if kw in content.lower()]}",
    }


def evaluate_skill(skill_path: str) -> dict:
    """评估技能质量"""
    skill = load_skill(skill_path)
    
    # 运行所有检查
    checks = [
        check_description_trigger(skill),
        check_no_workflow_in_desc(skill),
        check_token_efficiency(skill),
        check_reference_depth(skill),
        check_no_anti_patterns(skill),
        check_has_checklist(skill),
        check_has_progress_output(skill),
        check_rationalization_table(skill),
        check_clear_gates(skill),
    ]
    
    # 计算总分
    total_score = 0.0
    for check in checks:
        rule = next(r for r in RULES if r["id"] == check["rule"])
        if check["passed"]:
            total_score += rule["weight"]
    
    # 确定等级
    if total_score >= 0.9:
        grade = "A"
    elif total_score >= 0.7:
        grade = "B"
    elif total_score >= 0.5:
        grade = "C"
    else:
        grade = "D"
    
    return {
        "skill_path": skill_path,
        "total_score": round(total_score, 3),
        "grade": grade,
        "checks": checks,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python evaluate.py <skill-path>")
        sys.exit(1)
    
    skill_path = sys.argv[1]
    
    try:
        result = evaluate_skill(skill_path)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
