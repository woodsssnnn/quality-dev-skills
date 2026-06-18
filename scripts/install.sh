#!/bin/bash
# install.sh — quality-dev-skills 全局软链接安装
#
# 用法：
#   bash scripts/install.sh                    # 全局安装到 ~/.agents/skills/
#   bash scripts/install.sh quality-gate-workflow     # 安装单个
#   bash scripts/install.sh --update           # 更新（全量重新链接，不报错）
#
# 来源目录不绑定：git clone 到任意位置，在该目录下运行本脚本即可全局安装。
# 脚本基于自身位置自动定位源目录（$REPO_DIR/skills/）。
#
# 兼容性：Linux / macOS / Windows Git Bash
#
# 链接策略（隐式由 ln -s 处理，跨平台行为）：
#   - Linux / macOS：ln -s 创建标准 SymbolicLink
#   - Windows Git Bash：ln -s 实际创建 Windows Directory Junction（无需特权）
#   两者对应用层等价：都是 reparse point，写入任意一侧另一侧立即可见。
#   Windows 原生 PowerShell 用户请使用 install.ps1（其 symlink → junction → copy
#   三级降级是该平台的对应实现）。

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "========================================="
echo " quality-dev-skills install"
echo "========================================="
echo ""

UPDATE_MODE=false
SKILLS=()

for arg in "$@"; do
  case "$arg" in
    --update|-u)   UPDATE_MODE=true ;;
    --help|-h)
      echo "Usage: bash scripts/install.sh [skills...] [--update]"
      echo "  --update    Re-link all (idempotent, no error on overwrite)"
      echo "  skills: quality-gate-workflow skill-optimizer (default: all)"
      exit 0
      ;;
    *) SKILLS+=("$arg") ;;
  esac
done

TARGET="$HOME/.agents/skills"
echo "[install] mode=global target=$TARGET"

# 执行链接（link.sh 负责在 ~/.agents/skills/ 下建立软链接）
echo "[install] Linking..."
bash "$REPO_DIR/scripts/link.sh" "${SKILLS[@]}" || true

# 验证目标目录存在
if [ ! -d "$TARGET" ]; then
  mkdir -p "$TARGET"
fi

echo ""
echo "========================================="
echo " Install complete."
echo " Update: git pull && bash scripts/install.sh --update"
echo " Uninstall: bash scripts/uninstall.sh"
echo "========================================="
