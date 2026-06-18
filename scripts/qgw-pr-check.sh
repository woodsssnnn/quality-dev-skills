#!/usr/bin/env bash
# qgw-pr-check.sh — PR 质量检查入口脚本
#
# Usage:
#   bash scripts/qgw-pr-check.sh --skills "skills/api-design-review skills/db-migration-gate" --min-score B
#   bash scripts/qgw-pr-check.sh --skills "skills/quality-gate-workflow"
#
# Checks:
#   1. SKILL.md exists and has valid frontmatter
#   2. manifest-entry.json exists and is valid JSON
#   3. Evaluations directory has >= 3 scenarios
#   4. Python scripts pass py_compile
#   5. No third-party imports (stdlib only)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SKILLS=""
MIN_SCORE="B"
ERRORS=0

usage() {
    echo "Usage: $0 --skills '<space-separated skill paths>' [--min-score <A|B|C>]"
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --skills)
            SKILLS="$2"
            shift 2
            ;;
        --min-score)
            MIN_SCORE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

if [ -z "$SKILLS" ]; then
    echo "No skills specified, nothing to check."
    exit 0
fi

check_skill() {
    local skill_path="$1"
    local skill_dir="$REPO_ROOT/$skill_path"
    local skill_name
    skill_name="$(basename "$skill_path")"

    echo "========================================="
    echo "Checking skill: $skill_name ($skill_path)"
    echo "========================================="

    # 1. SKILL.md exists
    if [ ! -f "$skill_dir/SKILL.md" ]; then
        echo "  FAIL: SKILL.md not found"
        ERRORS=$((ERRORS + 1))
    else
        echo "  OK: SKILL.md exists"

        # Check frontmatter
        if head -1 "$skill_dir/SKILL.md" | grep -q "^---"; then
            echo "  OK: YAML frontmatter present"
        else
            echo "  FAIL: Missing YAML frontmatter"
            ERRORS=$((ERRORS + 1))
        fi
    fi

    # 2. manifest-entry.json
    if [ ! -f "$skill_dir/manifest-entry.json" ]; then
        echo "  WARN: manifest-entry.json not found (recommended)"
    else
        if python3 -c "import json; json.load(open('$skill_dir/manifest-entry.json'))" 2>/dev/null; then
            echo "  OK: manifest-entry.json is valid JSON"
        else
            echo "  FAIL: manifest-entry.json is invalid JSON"
            ERRORS=$((ERRORS + 1))
        fi
    fi

    # 3. Evaluations >= 3
    if [ -d "$skill_dir/evaluations" ]; then
        eval_count=$(find "$skill_dir/evaluations" -name "scenario-*.md" | wc -l)
        if [ "$eval_count" -ge 3 ]; then
            echo "  OK: $eval_count evaluation scenarios (>= 3)"
        else
            echo "  FAIL: Only $eval_count evaluation scenarios (need >= 3)"
            ERRORS=$((ERRORS + 1))
        fi
    else
        echo "  FAIL: evaluations/ directory not found"
        ERRORS=$((ERRORS + 1))
    fi

    # 4. Python syntax check
    if [ -d "$skill_dir/scripts" ]; then
        for py_file in "$skill_dir/scripts"/*.py; do
            [ -f "$py_file" ] || continue
            if python3 -m py_compile "$py_file" 2>/dev/null; then
                echo "  OK: $(basename "$py_file") syntax valid"
            else
                echo "  FAIL: $(basename "$py_file") syntax error"
                ERRORS=$((ERRORS + 1))
            fi
        done
    fi

    # 5. stdlib only check
    if [ -d "$skill_dir/scripts" ]; then
        for py_file in "$skill_dir/scripts"/*.py; do
            [ -f "$py_file" ] || continue
            # Check for common third-party imports
            bad_imports=$(grep -E "^import (requests|flask|django|fastapi|numpy|pandas|click|rich|pydantic|yaml|toml)" "$py_file" 2>/dev/null || true)
            if [ -n "$bad_imports" ]; then
                echo "  FAIL: $(basename "$py_file") has third-party imports: $bad_imports"
                ERRORS=$((ERRORS + 1))
            else
                echo "  OK: $(basename "$py_file") stdlib only"
            fi
        done
    fi

    echo ""
}

# Run checks for each skill
for skill in $SKILLS; do
    check_skill "$skill"
done

# Summary
echo "========================================="
if [ "$ERRORS" -gt 0 ]; then
    echo "PR check FAILED: $ERRORS error(s) found"
    exit 1
else
    echo "PR check PASSED: all skills OK"
    exit 0
fi
