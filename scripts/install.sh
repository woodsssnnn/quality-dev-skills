#!/bin/bash
# install.sh — quality-dev-skills 全局软链接安装
#
# 用法：
#   bash scripts/install.sh                    # 全局安装到 ~/.agents/skills/
#   bash scripts/install.sh quality-gate-workflow     # 安装单个
#   bash scripts/install.sh --update           # 更新（全量重新链接，不报错）
#   bash scripts/install.sh --init             # 一键安装：链接 + 工作区初始化 + 健康检查
#   bash scripts/install.sh --dry-run          # 预览安装动作，不执行
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

# ===== Preflight 硬性检查 =====
# 检测操作系统（用于输出平台对应的安装命令）
detect_os() {
  case "$(uname -s 2>/dev/null || echo unknown)" in
    Linux*)   echo "linux" ;;
    Darwin*)  echo "macos" ;;
    MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
    *)        echo "unknown" ;;
  esac
}

preflight_check() {
  local os
  os=$(detect_os)
  local missing=0

  echo "[preflight] 检查运行环境..."
  echo ""

  # 1. Python 3
  local python_cmd=""
  if command -v python3 >/dev/null 2>&1; then
    python_cmd="python3"
  elif command -v python >/dev/null 2>&1; then
    # 确认是 Python 3
    local py_ver
    py_ver=$(python -c "import sys; print(sys.version_info[0])" 2>/dev/null || echo "0")
    if [ "$py_ver" = "3" ]; then
      python_cmd="python"
    fi
  fi

  if [ -n "$python_cmd" ]; then
    echo "  ✅ Python 3: $($python_cmd --version 2>&1)"
  else
    echo "  ❌ Python 3 未找到"
    case "$os" in
      macos)
        echo "     brew install python3"
        echo "     或: https://www.python.org/downloads/"
        ;;
      linux)
        echo "     Ubuntu/Debian:  sudo apt install python3"
        echo "     Fedora/RHEL:    sudo dnf install python3"
        echo "     Arch:           sudo pacman -S python"
        ;;
      windows)
        echo "     winget install Python.Python.3.12"
        echo "     或: https://www.python.org/downloads/"
        echo "     安装时勾选 'Add Python to PATH'"
        ;;
      *)
        echo "     https://www.python.org/downloads/"
        ;;
    esac
    missing=1
  fi

  # 2. Git
  if command -v git >/dev/null 2>&1; then
    echo "  ✅ Git: $(git --version 2>&1)"
  else
    echo "  ❌ Git 未找到"
    case "$os" in
      macos)
        echo "     brew install git"
        echo "     或: xcode-select --install"
        ;;
      linux)
        echo "     Ubuntu/Debian:  sudo apt install git"
        echo "     Fedora/RHEL:    sudo dnf install git"
        echo "     Arch:           sudo pacman -S git"
        ;;
      windows)
        echo "     winget install Git.Git"
        echo "     或: https://git-scm.com/downloads"
        ;;
      *)
        echo "     https://git-scm.com/downloads"
        ;;
    esac
    missing=1
  fi

  echo ""

  if [ "$missing" -eq 1 ]; then
    echo "========================================="
    echo " ❌ 安装中止：请先安装以上缺失依赖"
    echo "========================================="
    echo ""
    echo " Python 3 和 Git 是 QGW 的硬性运行依赖："
    echo "   - Python 3: 确定性引擎、Hook 检查、报告生成"
    echo "   - Git:      版本控制、Hook 机制、commitSha 记录"
    echo ""
    echo " 安装完成后重新运行本脚本即可。"
    exit 1
  fi

  echo "[preflight] ✅ 环境检查通过"
  echo ""
}

# --update 模式跳过 preflight（已安装过说明依赖已就绪）
PREFLIGHT_SKIP=false
for arg in "$@"; do
  case "$arg" in
    --update|-u) PREFLIGHT_SKIP=true ;;
  esac
done

if [ "$PREFLIGHT_SKIP" = false ]; then
  preflight_check
fi

echo "========================================="
echo " quality-dev-skills install"
echo "========================================="
echo ""

UPDATE_MODE=false
INIT_MODE=false
DRY_RUN=false
SKILLS=()

for arg in "$@"; do
  case "$arg" in
    --update|-u)   UPDATE_MODE=true ;;
    --init)        INIT_MODE=true ;;
    --dry-run)     DRY_RUN=true ;;
    --help|-h)
      echo "Usage: bash scripts/install.sh [skills...] [--update] [--init] [--dry-run]"
      echo "  --update    Re-link all (idempotent, no error on overwrite)"
      echo "  --init      Full setup: link + workspace init + health check"
      echo "  --dry-run   Preview actions without executing"
      echo "  skills: quality-gate-workflow skill-optimizer (default: all)"
      exit 0
      ;;
    *) SKILLS+=("$arg") ;;
  esac
done

TARGET="$HOME/.agents/skills"
echo "[install] mode=global target=$TARGET"

if [ "$DRY_RUN" = true ]; then
  echo "[install] DRY RUN — no changes will be made"
  echo ""
  echo "[install] Would link skills to: $TARGET"
  SKILL_LIST="${SKILLS[*]:-all}"
  echo "[install] Skills to install: $SKILL_LIST"
  echo ""
  if [ "$INIT_MODE" = true ]; then
    echo "[install] Would initialize workspace: mkdir -p docs/{plans,verification,reports,sessions}"
    echo "[install] Would run health check: bash scripts/health-check.sh"
  fi
  echo ""
  echo "[install] Run without --dry-run to apply."
  exit 0
fi

# 验证目标目录存在
if [ ! -d "$TARGET" ]; then
  mkdir -p "$TARGET"
fi

# 执行链接（link.sh 负责在 ~/.agents/skills/ 下建立软链接）
echo "[install] Linking..."
LINK_EXIT=0
bash "$REPO_DIR/scripts/link.sh" "${SKILLS[@]}" || LINK_EXIT=$?
if [ "$LINK_EXIT" -ne 0 ]; then
  echo ""
  echo "[install] ⚠️  链接步骤有错误（退出码 $LINK_EXIT），请检查上方输出"
fi

# --init 模式：额外执行工作区初始化和健康检查
if [ "$INIT_MODE" = true ]; then
  echo ""
  echo "[install] Initializing workspace..."
  
  # 创建工作区目录（如果不存在）
  for dir in docs/plans docs/verification docs/reports docs/sessions; do
    if [ ! -d "$dir" ]; then
      mkdir -p "$dir"
      echo "[install]   Created: $dir"
    else
      echo "[install]   Exists: $dir"
    fi
  done
  
  # 运行健康检查
  if [ -f "$REPO_DIR/skills/quality-gate-workflow/scripts/health-check.sh" ]; then
    echo ""
    echo "[install] Running health check..."
    bash "$REPO_DIR/skills/quality-gate-workflow/scripts/health-check.sh" || echo "[install] Health check completed with warnings"
  fi
fi

echo ""
echo "========================================="
echo " ✅ Install complete."
echo "========================================="
echo ""
echo " Next steps:"
echo "   1. 在项目根目录创建 .qgw/ 目录（可选，用于项目定制）"
echo "   2. 在 AI 对话中说\"帮我实现这个需求\"开始使用"
echo "   3. 或使用 --preset feature 启动完整流程"
echo ""
echo " Update: git pull && bash scripts/install.sh --update"
echo " Uninstall: bash scripts/uninstall.sh"
echo "========================================="
