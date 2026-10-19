#!/usr/bin/env bash
# ==========================================================================
# check-banned-terms.sh — 仓库中立性门禁（CI 与本地共用）
#
# 扫描所有 git 跟踪文件，确保不出现来源项目品牌词。本仓库定位为中立、
# 开放的通用框架，不得携带任何来源项目的品牌/术语残留。
#
# 实现说明：禁词模式由片段在运行时拼装，避免本脚本自身被扫描命中。
# 后续需要扩展禁词时，继续以片段方式追加到 PATTERN。
#
# 用法:   bash scripts/check-banned-terms.sh
# 退出码: 0 = 通过；1 = 发现禁词；2 = 环境错误
# ==========================================================================
set -uo pipefail

cd "$(git rev-parse --show-toplevel)" || exit 2

_a="${BANNED_A:-ep}"; _b="${BANNED_B:-ros}"
_c="${BANNED_C:-je}"; _d="${BANNED_D:-cn}"
PATTERN="${_a}${_b}|${_c}${_d}"

hits="$(git grep -iInE "$PATTERN" -- . || true)"
if [ -n "$hits" ]; then
  echo "❌ 发现来源项目品牌词残留（文件:行号:内容）："
  printf '%s\n' "$hits"
  echo ""
  echo "请将这些措辞替换为中立表述后重新提交。"
  exit 1
fi
echo "✅ 中立性检查通过：未发现来源项目品牌词"
