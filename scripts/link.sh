#!/bin/bash
# link.sh — 建立软链接：source → ~/.agents/skills/<name>
#
# 用法：
#   bash scripts/link.sh <skill-name>          # 链接单个技能
#   bash scripts/link.sh                       # 链接 skills/ 下所有技能
#
# 兼容性：
#   Linux / macOS / Windows Git Bash
#   重复运行安全（先删旧链再重建）

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_SRC="$REPO_DIR/skills"
AGENT_SKILLS_DIR="$HOME/.agents/skills"

# 确保目标目录存在
mkdir -p "$AGENT_SKILLS_DIR"

link_one() {
  local name="$1"
  local src="$SKILLS_SRC/$name"

  if [ ! -f "$src/SKILL.md" ]; then
    echo "[link] ❌ $name: SKILL.md 不存在于 $src，跳过"
    return 1
  fi

  local target="$AGENT_SKILLS_DIR/$name"

  # 清理旧链接/目录
  if [ -L "$target" ] || [ -d "$target" ]; then
    rm -rf "$target"
  fi

  # 建立软链接
  # Windows Git Bash 的 ln -s 实际创建 Windows 目录链接（junction），
  # Linux/macOS 创建标准符号链接 — 两者效果一致，均可跨平台工作
  ln -s "$src" "$target"

  if [ -L "$target" ] || [ -d "$target" ]; then
    echo "[link] ✅ $name → $target"
  else
    echo "[link] ❌ $name: 链接创建失败"
    return 1
  fi
}

if [ $# -ge 1 ]; then
  # 链接指定技能
  for skill in "$@"; do
    link_one "$skill"
  done
else
  # 链接 skills/ 下所有包含 SKILL.md 的目录
  echo "[link] 🔍 发现 skills/ 下所有技能..."
  for dir in "$SKILLS_SRC"/*/; do
    name="$(basename "$dir")"
    if [ -f "$dir/SKILL.md" ]; then
      link_one "$name"
    fi
  done
fi

echo "[link] ✅ 全部完成"
