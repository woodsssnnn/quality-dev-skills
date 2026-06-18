#!/bin/bash
# hook-install.sh — 质量门禁 Hook 安装/重新安装/卸载
#
# 用途：将 verify-checkpoint.sh 注册为 AI 工具的 PreToolUse / PreCommit Hook。
#       检测当前工具并写入对应的配置文件。
#
# 用法：
#   bash hook-install.sh              # 安装（自动检测工具，先卸载旧配置）
#   bash hook-install.sh --force      # 强制重新安装（先卸载再安装）
#   bash hook-install.sh --dry-run    # 仅显示将要写入的配置，不写文件
#   bash hook-install.sh --mode=strict|warn|off  # 设置 Hook 检查模式
#
# 检查逻辑：
#   1. 检测当前 AI 工具环境
#   2. 定位对应的 settings 文件（.claude/settings.json / settings.local.json 等）
#   3. 检查是否已安装（避免重复写入）
#   4. 写入或更新 Hook 配置
#   5. 验证配置生效

HOOK_SCRIPT="verify-checkpoint.sh"

# 从脚本自身位置推断技能根目录（兼容 Windows/macOS/Linux）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

HOOK_PATH="$SKILL_DIR/scripts/$HOOK_SCRIPT"

# 构建 Hook 配置 JSON（使用 heredoc 确保变量展开）
HOOK_CONFIG_ENTRY=$(cat <<-HOOKJSON
{
      "command": "bash ${HOOK_PATH}",
      "matcher": "Bash",
      "hooks": ["git commit", "PreToolUse"]
    }
HOOKJSON
)

# 已知的工具 settings 配置路径（按优先级排序）
KNOWN_SETTINGS=(
    ".claude/settings.local.json"   # 项目级 local（最高优先级，CI/CD 时忽略）
    ".claude/settings.json"         # 项目级
    "$HOME/.claude/settings.json"   # 用户全局
)

# temp files for --dry-run
DRY_RUN=false
FORCE=false
HOOK_MODE=""

for arg in "$@"; do
    case "$arg" in
        --force) FORCE=true ;;
        --dry-run) DRY_RUN=true ;;
        --mode=*) HOOK_MODE="${arg#--mode=}" ;;
    esac
done

# 验证 --mode 值
if [ -n "$HOOK_MODE" ]; then
    case "$HOOK_MODE" in
        strict|warn|off) ;;
        *) echo "[hook-install] ❌ 无效的 --mode 值: $HOOK_MODE（有效值: strict, warn, off）"; exit 1 ;;
    esac
fi

# ===== 路径解析 =====

echo "[hook-install] 🔍 质量门禁 Hook 安装..."

# 技能自身路径前置检查
if [ ! -f "$HOOK_PATH" ]; then
    echo "[hook-install] ❌ Hook 脚本不存在: $HOOK_PATH"
    echo "   技能目录: $SKILL_DIR"
    echo "   请确认脚本在正确的位置运行"
    exit 1
fi

# ===== 工具链检查 =====

# Python 检测（用于可靠的 JSON 操作）
PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" &>/dev/null; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo "[hook-install] ❌ 未找到 Python (python3/python)，JSON 操作需要 Python 支持"
    exit 1
fi

# ===== 工具检测 =====

DETECTED_TOOL=""
if [ -f ".claude/settings.json" ] || [ -f "$HOME/.claude/settings.json" ]; then
    DETECTED_TOOL="claude-code"
fi

if [ -n "$DETECTED_TOOL" ]; then
    echo "[hook-install] ✅ 检测到工具: $DETECTED_TOOL"
else
    echo "[hook-install] ⚠ 未检测到已知 AI 工具配置目录。"
    echo "   已知工具：Claude Code (.claude/settings.json)"
    echo "   如果使用其他工具，请手动安装 Hook："
    echo "     将以下配置写入工具对应的 settings 文件："
    echo "     ${HOOK_CONFIG_ENTRY//$'\n'/ }"
    exit 0
fi

# ===== 查找已有的 Hook 配置并卸载 =====

INSTALLED=false
INSTALLED_FILE=""
for sf in "${KNOWN_SETTINGS[@]}"; do
    eval sf_expanded="$sf"
    if [ -f "$sf_expanded" ] && grep -q "$HOOK_SCRIPT" "$sf_expanded" 2>/dev/null; then
        INSTALLED=true
        INSTALLED_FILE="$sf_expanded"
        break
    fi
done

if [ "$INSTALLED" = true ] && [ "$FORCE" != true ]; then
    echo "[hook-install] ℹ  检测到已有 Hook 配置于: $INSTALLED_FILE"
    echo "   如需重新安装，请先运行 hook-uninstall.sh 或使用 --force 参数"
    exit 0
fi

if [ "$INSTALLED" = true ] && [ "$FORCE" = true ]; then
    echo "[hook-install] 🔄 检测到已有配置，--force 模式：先卸载旧配置"
    # 调用 hook-uninstall.sh 清理
    uninstall_script="$SKILL_DIR/scripts/hook-uninstall.sh"
    if [ -f "$uninstall_script" ]; then
        bash "$uninstall_script" --quiet
    else
        # 手动清理：从所有 settings 文件中移除
        for sf in "${KNOWN_SETTINGS[@]}"; do
            eval sf_expanded="$sf"
            if [ -f "$sf_expanded" ]; then
                "$PYTHON" -c "
import json, sys
try:
    with open('$sf_expanded', 'r') as f:
        cfg = json.load(f)
    hooks = cfg.get('hooks', {}).get('PreToolUse', [])
    filtered = [h for h in hooks if '$HOOK_SCRIPT' not in h.get('command', '')]
    if len(filtered) != len(hooks):
        cfg['hooks']['PreToolUse'] = filtered
        with open('$sf_expanded', 'w') as f:
            json.dump(cfg, f, indent=2)
        print(f'  已从 $sf_expanded 清理')
except Exception as e:
    print(f'  ⚠  $sf_expanded 解析失败: {e}')
" 2>/dev/null || true
            fi
        done
    fi
fi

# ===== 选择安装目标文件 =====

# 优先级：project local > project > user global
TARGET_FILE=""
for sf in "${KNOWN_SETTINGS[@]}"; do
    eval sf_expanded="$sf"
    # 优先使用已存在的 settings 文件
    if [ -f "$sf_expanded" ]; then
        TARGET_FILE="$sf_expanded"
        break
    fi
done

if [ -z "$TARGET_FILE" ]; then
    # 都不存在，创建项目级 settings.json
    TARGET_FILE=".claude/settings.json"
    mkdir -p ".claude"
    echo "{}" > "$TARGET_FILE"
fi

echo "[hook-install] 📝 安装到: $TARGET_FILE"

if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "=== 将要写入的配置 ==="
    echo "文件: $TARGET_FILE"
    echo "内容: 在 hooks.PreToolUse 数组中添加以下条目"
    echo "$HOOK_CONFIG_ENTRY"
    echo ""
    echo "=== 干运行完成，未写入任何文件 ==="
    exit 0
fi

# ===== 写入配置 =====

# 使用 Python 精确写入 JSON（避免 shell JSON 拼装错误）
"$PYTHON" -c "
import json, sys, os

target = '$TARGET_FILE'
hook_cmd = '$HOOK_PATH'
entry = json.loads('$HOOK_CONFIG_ENTRY')
hook_mode = '$HOOK_MODE'

# 读取或创建配置
try:
    with open(target, 'r') as f:
        cfg = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    cfg = {}

# 确保 hooks.PreToolUse 存在
if 'hooks' not in cfg:
    cfg['hooks'] = {}
if 'PreToolUse' not in cfg['hooks']:
    cfg['hooks']['PreToolUse'] = []

# 检查是否已存在（避免 duplicate）
hooks_list = cfg['hooks']['PreToolUse']
already = any(h.get('command', '') == hook_cmd for h in hooks_list)
if already:
    print('  ℹ  Hook 配置已存在，跳过写入')
else:
    hooks_list.append(entry)
    cfg['hooks']['PreToolUse'] = hooks_list
    
    # 写入文件
    with open(target, 'w') as f:
        json.dump(cfg, f, indent=2)
    print('  ✅ Hook 配置已写入')

# 写入 env.QGW_HOOK_MODE（如果指定了 --mode）
if hook_mode:
    if 'env' not in cfg:
        cfg['env'] = {}
    cfg['env']['QGW_HOOK_MODE'] = hook_mode
    with open(target, 'w') as f:
        json.dump(cfg, f, indent=2)
    print(f'  ✅ QGW_HOOK_MODE={hook_mode} 已写入')

# 最终验证
with open(target, 'r') as f:
    final = json.load(f)
final_cmds = [h.get('command', '') for h in final.get('hooks', {}).get('PreToolUse', [])]
if any(hook_cmd in cmd for cmd in final_cmds):
    print('  ✅ 验证通过')
else:
    print('  ❌ 验证失败：写入后未找到配置')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "[hook-install] ✅ Hook 安装完成"
    echo "   下次 git commit 时将自动触发验收检查"
    echo "   如需卸载，执行: bash $SKILL_DIR/scripts/hook-uninstall.sh"
else
    echo "[hook-install] ❌ Hook 安装失败"
    exit 1
fi
