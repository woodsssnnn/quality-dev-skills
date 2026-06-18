#!/bin/bash
# hook-uninstall.sh — 质量门禁 Hook 卸载
#
# 用途：从 AI 工具的 settings 配置中移除 verify-checkpoint.sh Hook 条目。
#
# 用法：
#   bash hook-uninstall.sh             # 卸载（交互模式，显示发现和清理结果）
#   bash hook-uninstall.sh --quiet     # 静默卸载（供 hook-install.sh --force 调用）
#   bash hook-uninstall.sh --dry-run   # 仅显示将清理什么，不操作

HOOK_SCRIPT="verify-checkpoint.sh"

# 从脚本自身位置推断技能根目录（兼容 Windows/macOS/Linux）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Python 检测（用于可靠的 JSON 操作）
PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" &>/dev/null; then
        PYTHON="$candidate"
        break
    fi
done

QUIET=false
DRY_RUN=false
if [ "$1" = "--quiet" ]; then
    QUIET=true
elif [ "$1" = "--dry-run" ]; then
    DRY_RUN=true
fi

if [ "$QUIET" = false ]; then
    echo "[hook-uninstall] 🔍 质量门禁 Hook 卸载..."
fi

# 已知的 settings 路径
KNOWN_SETTINGS=(
    ".claude/settings.local.json"
    ".claude/settings.json"
    "$HOME/.claude/settings.json"
)

FOUND=false
REMOVED_COUNT=0

for sf in "${KNOWN_SETTINGS[@]}"; do
    eval sf_expanded="$sf"
    if [ ! -f "$sf_expanded" ]; then
        continue
    fi

    # 检查是否包含我们的 Hook
    if ! grep -q "$HOOK_SCRIPT" "$sf_expanded" 2>/dev/null; then
        continue
    fi

    FOUND=true

    if [ "$DRY_RUN" = true ]; then
        if [ "$QUIET" = false ]; then
            echo "  📋 $sf_expanded — 将移除 verify-checkpoint.sh Hook 条目"
        fi
        REMOVED_COUNT=$((REMOVED_COUNT + 1))
        continue
    fi

    if [ -z "$PYTHON" ]; then
        # 降级：使用 grep/sed（不精确，但能工作）
        echo "  ⚠  Python 不可用，使用 sed 降级清理 $sf_expanded"
        # 创建一个临时文件，过滤掉包含 verify-checkpoint 的行及其周围的 JSON 结构
        # 注意：这种方式可能留下无效 JSON，建议安装 Python 后重试
        if [ "$QUIET" = false ]; then
            echo "  ⚠  建议安装 Python 后重试以确保 JSON 完整性"
        fi
        # 清理整行
        tmpfile=$(mktemp)
        grep -v "$HOOK_SCRIPT" "$sf_expanded" > "$tmpfile" && mv "$tmpfile" "$sf_expanded"
    else
        "$PYTHON" -c "
import json, sys

target = '$sf_expanded'
try:
    with open(target, 'r') as f:
        cfg = json.load(f)
except (json.JSONDecodeError, FileNotFoundError) as e:
    print(f'  ⚠  跳过 $sf_expanded: {e}')
    sys.exit(0)

hooks = cfg.get('hooks', {}).get('PreToolUse', [])
original_len = len(hooks)
filtered = [h for h in hooks if '$HOOK_SCRIPT' not in h.get('command', '')]

if len(filtered) != original_len:
    cfg['hooks']['PreToolUse'] = filtered
    with open(target, 'w') as f:
        json.dump(cfg, f, indent=2)
    print(f'  ✅ $sf_expanded — 已移除 Hook 条目')
else:
    print(f'  ℹ  $sf_expanded — 无相关配置')
" 2>/dev/null
    fi

    REMOVED_COUNT=$((REMOVED_COUNT + 1))
done

if [ "$FOUND" = false ]; then
    if [ "$QUIET" = false ]; then
        echo "[hook-uninstall] ℹ  未找到已安装的 Hook 配置，无需卸载"
    fi
    exit 0
fi

if [ "$DRY_RUN" = true ]; then
    echo "[hook-uninstall] ℹ  干运行完成，发现 $REMOVED_COUNT 个配置位置将被清理"
    exit 0
fi

if [ "$QUIET" = false ]; then
    echo "[hook-uninstall] ✅ Hook 已卸载 ($REMOVED_COUNT 个配置被清理)"
    echo "   下次 git commit 时将不再自动触发验收检查"
    echo "   如需重新安装，执行: bash $SKILL_DIR/scripts/hook-install.sh"
fi
exit 0
