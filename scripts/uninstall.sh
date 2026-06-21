#!/bin/bash
# uninstall.sh — 从 ~/.agents/skills/ 移除技能
#
# 用法：
#   bash scripts/uninstall.sh                  # 卸载全部
#   bash scripts/uninstall.sh quality-gate-workflow   # 卸载单个
#
# 兼容两种历史安装：
#   - 软链接安装（当前标准方式，ln -s / Junction）→ 读取链接源后删除链接
#   - 早期复制安装（实体目录）→ 直接删除目录
# 脚本会先判断类型再报告，让用户清楚看到之前是什么安装方式。
#
# 兼容性：Linux / macOS / Windows Git Bash

set -euo pipefail

AGENT_SKILLS_DIR="$HOME/.agents/skills"

# --help 支持
for arg in "$@"; do
  case "$arg" in
    --help|-h)
      echo "uninstall.sh — 从 ~/.agents/skills/ 移除技能"
      echo ""
      echo "用法:"
      echo "  bash scripts/uninstall.sh                  # 卸载全部"
      echo "  bash scripts/uninstall.sh quality-gate-workflow   # 卸载单个"
      echo ""
      echo "兼容软链接安装（ln -s / Junction）和早期复制安装。"
      exit 0
      ;;
  esac
done

remove_one() {
  local name="$1"
  local target="$AGENT_SKILLS_DIR/$name"

  if [ -L "$target" ]; then
    # 软链接安装（当前标准方式）
    local src
    src="$(readlink "$target")"
    echo "[uninstall] 🔗 已移除软链接: $name -> $src"
    rm -f "$target"
  elif [ -d "$target" ]; then
    # 实体目录（早期复制安装遗留）
    echo "[uninstall] 📁 已移除复制目录(旧安装): $name"
    rm -rf "$target"
  else
    echo "[uninstall] ℹ  $name 未安装，跳过"
    return 0
  fi
}

if [ $# -ge 1 ]; then
  for skill in "$@"; do
    remove_one "$skill"
  done
else
  echo "[uninstall] 🔍 扫描已安装的技能..."
  for entry in "$AGENT_SKILLS_DIR"/*; do
    [ -e "$entry" ] || continue  # 空目录时通配符不展开
    name="$(basename "$entry")"
    remove_one "$name"
  done
fi

echo "[uninstall] ✅ 全部完成"
