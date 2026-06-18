#!/usr/bin/env bash
# run-evals.sh — 端到端回归测试入口
#
# 用法:
#   bash scripts/run-evals.sh          # 完整运行
#   bash scripts/run-evals.sh --quick  # 跳过单元测试，只跑冒烟测试
#
# 退出码:
#   0 = 全部通过
#   1 = 有失败

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  echo -e "  ${GREEN}✅ $1${NC}"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  echo -e "  ${RED}❌ $1${NC}"
}

skip() {
  SKIP_COUNT=$((SKIP_COUNT + 1))
  echo -e "  ${YELLOW}⏭️  $1${NC}"
}

echo "========================================="
echo " QGW 端到端回归测试"
echo "========================================="
echo ""

# ===== Phase 1: Python 单元测试 =====
echo "📋 Phase 1: Python 单元测试"
echo "-----------------------------------------"

# gate-enforcer.py 测试
if command -v python3 &>/dev/null; then
  PY=python3
elif command -v python &>/dev/null; then
  PY=python
else
  skip "Python 不可用，跳过单元测试"
  PY=""
fi

if [ -n "$PY" ]; then
  # 检查 pytest 是否可用
  if $PY -m pytest --version &>/dev/null 2>&1; then
    echo "  运行 gate-enforcer.py 测试..."
    if (cd "$REPO_DIR/skills/quality-gate-workflow/scripts" && $PY -m pytest tests/ -v --tb=short 2>&1); then
      pass "gate-enforcer.py 单元测试全部通过"
    else
      fail "gate-enforcer.py 单元测试有失败"
    fi
  else
    skip "pytest 未安装，跳过 gate-enforcer.py 单元测试"
  fi
fi

echo ""

# ===== Phase 2: gate-enforcer.py CLI 冒烟测试 =====
echo "📋 Phase 2: gate-enforcer.py CLI 冒烟测试"
echo "-----------------------------------------"

if [ -n "$PY" ]; then
  ENFORCER="$REPO_DIR/skills/quality-gate-workflow/scripts/gate-enforcer.py"

  # 创建临时工作目录
  TMPDIR=$(mktemp -d)
  trap "rm -rf $TMPDIR" EXIT
  cd "$TMPDIR"

  # 创建必要的目录
  mkdir -p docs/plans docs/verification docs/reports docs/sessions

  # 测试 init
  if $PY "$ENFORCER" init --gate gate1 --mode prd >/dev/null 2>&1; then
    pass "init --gate gate1 成功"
  else
    fail "init --gate gate1 失败"
  fi

  # 测试 status
  if $PY "$ENFORCER" status >/dev/null 2>&1; then
    pass "status 查询成功"
  else
    fail "status 查询失败"
  fi

  # 测试 enter P0
  if $PY "$ENFORCER" enter P0 2>/dev/null | grep -q "ALLOW"; then
    pass "enter P0 返回 ALLOW"
  else
    fail "enter P0 未返回 ALLOW"
  fi

  # 测试 complete P0
  if $PY "$ENFORCER" complete P0 2>/dev/null | grep -q "OK"; then
    pass "complete P0 返回 OK"
  else
    fail "complete P0 未返回 OK"
  fi

  # 测试 self-check
  if $PY "$ENFORCER" self-check >/dev/null 2>&1; then
    pass "self-check 成功"
  else
    fail "self-check 失败"
  fi

  # 测试 resume
  if $PY "$ENFORCER" resume >/dev/null 2>&1; then
    pass "resume 成功"
  else
    fail "resume 失败"
  fi

  # 测试 prd-changed
  if $PY "$ENFORCER" prd-changed --impact cosmetic >/dev/null 2>&1; then
    pass "prd-changed --impact cosmetic 成功"
  else
    fail "prd-changed --impact cosmetic 失败"
  fi

  cd "$REPO_DIR"
else
  skip "Python 不可用，跳过 CLI 冒烟测试"
fi

echo ""

# ===== Phase 3: evaluate.py 冒烟测试 =====
echo "📋 Phase 3: evaluate.py 冒烟测试"
echo "-----------------------------------------"

if [ -n "$PY" ]; then
  EVALUATOR="$REPO_DIR/skills/skill-optimizer/scripts/evaluate.py"

  if [ -f "$EVALUATOR" ]; then
    # 对 quality-gate-workflow 进行评分
    if $PY "$EVALUATOR" "$REPO_DIR/skills/quality-gate-workflow" >/dev/null 2>&1; then
      pass "evaluate.py 对 quality-gate-workflow 评分成功"
    else
      fail "evaluate.py 对 quality-gate-workflow 评分失败"
    fi

    # 对 skill-optimizer 进行评分
    if $PY "$EVALUATOR" "$REPO_DIR/skills/skill-optimizer" >/dev/null 2>&1; then
      pass "evaluate.py 对 skill-optimizer 评分成功"
    else
      fail "evaluate.py 对 skill-optimizer 评分失败"
    fi
  else
    skip "evaluate.py 不存在"
  fi
else
  skip "Python 不可用，跳过 evaluate.py 冒烟测试"
fi

echo ""

# ===== Phase 4: Shell 脚本语法检查 =====
echo "📋 Phase 4: Shell 脚本语法检查"
echo "-----------------------------------------"

for sh_file in "$REPO_DIR"/scripts/*.sh; do
  if [ -f "$sh_file" ]; then
    if bash -n "$sh_file" 2>/dev/null; then
      pass "$(basename "$sh_file") 语法正确"
    else
      fail "$(basename "$sh_file") 语法错误"
    fi
  fi
done

# 检查 QGW 脚本
for sh_file in "$REPO_DIR"/skills/quality-gate-workflow/scripts/*.sh; do
  if [ -f "$sh_file" ]; then
    if bash -n "$sh_file" 2>/dev/null; then
      pass "$(basename "$sh_file") 语法正确"
    else
      fail "$(basename "$sh_file") 语法错误"
    fi
  fi
done

echo ""

# ===== Phase 5: JSON 格式验证 =====
echo "📋 Phase 5: JSON 格式验证"
echo "-----------------------------------------"

if [ -n "$PY" ]; then
  JSON_ERRORS=0
  while IFS= read -r -d '' json_file; do
    if ! $PY -c "import json; json.load(open('$json_file'))" 2>/dev/null; then
      fail "$(basename "$json_file") JSON 格式无效"
      JSON_ERRORS=$((JSON_ERRORS + 1))
    fi
  done < <(find "$REPO_DIR" -name "*.json" -not -path "*/node_modules/*" -not -path "*/.git/*" -print0)

  if [ "$JSON_ERRORS" -eq 0 ]; then
    pass "所有 JSON 文件格式有效"
  fi
else
  skip "Python 不可用，跳过 JSON 验证"
fi

echo ""

# ===== 汇总 =====
echo "========================================="
TOTAL=$((PASS_COUNT + FAIL_COUNT + SKIP_COUNT))
echo " 📊 总计: $TOTAL | ✅ 通过: $PASS_COUNT | ❌ 失败: $FAIL_COUNT | ⏭️  跳过: $SKIP_COUNT"
echo "========================================="

if [ "$FAIL_COUNT" -gt 0 ]; then
  echo -e "${RED}回归测试失败 ($FAIL_COUNT 项)${NC}"
  exit 1
else
  echo -e "${GREEN}回归测试全部通过${NC}"
  exit 0
fi
