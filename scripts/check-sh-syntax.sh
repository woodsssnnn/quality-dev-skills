#!/bin/bash
# check-sh-syntax.sh — 批量检查 .sh 脚本语法
cd "$(dirname "$0")/.." || exit 1
pass=0
fail=0
for f in scripts/*.sh skills/*/scripts/*.sh; do
    [ -f "$f" ] || continue
    if bash -n "$f" 2>/dev/null; then
        echo "  PASS $f"
        pass=$((pass+1))
    else
        echo "  FAIL $f"
        bash -n "$f"
        fail=$((fail+1))
    fi
done
echo ""
echo "Shell syntax: $pass passed, $fail failed"
exit $fail
