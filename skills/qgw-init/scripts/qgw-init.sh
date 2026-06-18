#!/usr/bin/env bash
# qgw-init.sh — 非交互式 QGW 项目初始化
#
# 用法: bash qgw-init.sh [options]
#   --platform claude|codex|opencode|mimo|general  平台（默认自动检测）
#   --mode lite|full|ultra                          工作流模式（默认 full）
#   --with-prd <name>                               创建PRD目录（可选）
#   --yes                                            非交互模式（跳过确认）
#   --force                                          覆盖已有 .qgw/ 目录
#   --help                                           显示帮助
#
# 示例:
#   bash qgw-init.sh                              # 自动检测平台，full 模式
#   bash qgw-init.sh --platform claude --mode lite
#   bash qgw-init.sh --platform codex --with-prd user-auth --yes
#   bash qgw-init.sh --force                       # 覆盖已有配置

set -euo pipefail

# ===== 默认值 =====
PLATFORM=""
MODE="full"
PRD_NAME=""
NON_INTERACTIVE=0
FORCE=0

# ===== 颜色输出 =====
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

info()    { echo -e "${BLUE}ℹ️  $*${NC}"; }
success() { echo -e "${GREEN}✅ $*${NC}"; }
warn()    { echo -e "${YELLOW}⚠️  $*${NC}"; }
error()   { echo -e "${RED}❌ $*${NC}"; }

# ===== 参数解析 =====
show_help() {
    echo "qgw-init.sh — 非交互式 QGW 项目初始化"
    echo ""
    echo "用法: bash qgw-init.sh [options]"
    echo ""
    echo "选项:"
    echo "  --platform claude|codex|opencode|mimo|general  平台（默认自动检测）"
    echo "  --mode lite|full|ultra                          工作流模式（默认 full）"
    echo "  --with-prd <name>                               创建 PRD 目录"
    echo "  --yes                                            非交互模式"
    echo "  --force                                          覆盖已有 .qgw/"
    echo "  --help                                           显示帮助"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --mode)
            MODE="$2"
            shift 2
            ;;
        --with-prd)
            PRD_NAME="$2"
            shift 2
            ;;
        --yes)
            NON_INTERACTIVE=1
            shift
            ;;
        --force)
            FORCE=1
            shift
            ;;
        --help|-h)
            show_help
            ;;
        *)
            error "未知参数: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

# ===== 参数验证 =====
if [[ -n "$PLATFORM" ]]; then
    case "$PLATFORM" in
        claude|codex|opencode|mimo|general) ;;
        *)
            error "无效平台: $PLATFORM"
            echo "可选值: claude, codex, opencode, mimo, general"
            exit 1
            ;;
    esac
fi

case "$MODE" in
    lite|full|ultra) ;;
    *)
        error "无效模式: $MODE"
        echo "可选值: lite, full, ultra"
        exit 1
        ;;
esac

# ===== Step 1: 环境检测 =====
echo ""
echo "========================================="
echo " QGW Init — 项目初始化"
echo "========================================="
echo ""

info "Step 1: 环境检测..."
echo ""

# 自动检测平台
if [[ -z "$PLATFORM" ]]; then
    if [[ -d ".claude" ]]; then
        PLATFORM="claude"
    elif [[ -f "AGENTS.md" ]] && grep -qi "codex" "AGENTS.md" 2>/dev/null; then
        PLATFORM="codex"
    elif ls opencode.config.* >/dev/null 2>&1; then
        PLATFORM="opencode"
    elif [[ -d ".mimo" ]]; then
        PLATFORM="mimo"
    else
        PLATFORM="general"
    fi
    info "自动检测平台: $PLATFORM"
fi

# Python 检测
PYTHON_CMD=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
    success "Python 3: $(python3 --version 2>/dev/null)"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
    success "Python: $(python --version 2>/dev/null)"
else
    warn "Python 未找到（gate-enforcer、health-check 详细模式将不可用）"
fi

# Git 检测
if [[ -d ".git" ]]; then
    success "Git 仓库已检测到"
else
    warn "Git 仓库未检测到（Hook 功能不可用）"
fi

# 已有 .qgw/ 检测
if [[ -d ".qgw" ]]; then
    if [[ "$FORCE" -eq 1 ]]; then
        warn "已有 .qgw/ 目录，--force 模式将覆盖"
    elif [[ "$NON_INTERACTIVE" -eq 1 ]]; then
        warn "已有 .qgw/ 目录，非交互模式将合并配置"
    else
        warn "已有 .qgw/ 目录，使用 --force 覆盖或 --yes 合并"
    fi
fi

echo ""

# ===== Step 2: 确认配置 =====
info "Step 2: 初始化配置"
echo ""
echo "  平台:     $PLATFORM"
echo "  模式:     $MODE"
echo "  PRD:      ${PRD_NAME:-未创建}"
echo ""

if [[ "$NON_INTERACTIVE" -eq 0 ]]; then
    read -rp "确认以上配置？(Y/n) " confirm
    if [[ "$confirm" =~ ^[Nn] ]]; then
        info "已取消初始化"
        exit 0
    fi
fi

# ===== Step 3: 创建 .qgw/ 目录 =====
info "Step 3: 创建 .qgw/ 目录..."
echo ""

mkdir -p .qgw

# 生成 config.json
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%S")

# 根据模式设置引擎参数
ENGINE_ENABLED="true"
ENGINE_STRICT="true"
case "$MODE" in
    lite)
        ENGINE_STRICT="false"
        ;;
    ultra)
        ENGINE_STRICT="true"
        ;;
    full)
        ENGINE_STRICT="true"
        ;;
esac

cat > .qgw/config.json << CONFIGEOF
{
  "platform": "$PLATFORM",
  "mode": "$MODE",
  "language": "zh",
  "hooks": { "mode": "strict" },
  "engine": {
    "enabled": $ENGINE_ENABLED,
    "strict_mode": $ENGINE_STRICT,
    "state_file": "docs/.qgw-engine-state.json",
    "checkpoint_dir": "docs/.qgw-checkpoints"
  },
  "initialized": "$TIMESTAMP",
  "version": "0.8.0.0"
}
CONFIGEOF

success ".qgw/config.json 已生成"

# 生成 constitution.md
if [[ ! -f ".qgw/constitution.md" ]] || [[ "$FORCE" -eq 1 ]]; then
    cat > .qgw/constitution.md << 'CONSTITUTIONEOF'
# 项目 Constitution

## 需求解析约束

<!-- 在此定义项目特有的需求解析规则 -->

- 所有需求必须明确标注优先级（P0/P1/P2）
- 功能性需求必须包含验收标准
- 非功能性需求必须量化指标
CONSTITUTIONEOF
    success ".qgw/constitution.md 已生成"
else
    info ".qgw/constitution.md 已存在，跳过"
fi

echo ""

# ===== Step 4: 创建 docs/ 目录 =====
info "Step 4: 创建 docs/ 产出物目录..."
echo ""

for dir in plans verification reports sessions; do
    target="docs/$dir"
    if [[ -d "$target" ]]; then
        info "docs/$dir/ 已存在"
    else
        mkdir -p "$target"
        success "创建 docs/$dir/"
    fi
done

echo ""

# ===== Step 5: PRD 目录（可选） =====
if [[ -n "$PRD_NAME" ]]; then
    info "Step 5: 创建 PRD 目录..."
    echo ""

    prd_dir="docs/prd/$PRD_NAME"
    mkdir -p "$prd_dir/verification"

    # 生成 PRD 模板
    if [[ ! -f "$prd_dir/prd.md" ]] || [[ "$FORCE" -eq 1 ]]; then
        cat > "$prd_dir/prd.md" << PRDEOF
# $PRD_NAME — 产品需求文档

## 概述

<!-- 需求背景和目标 -->

## 功能需求

### P0（必须）

- [ ] 需求 1

### P1（重要）

- [ ] 需求 2

### P2（可选）

- [ ] 需求 3

## 非功能需求

- 性能:
- 安全:
- 可用性:

## 验收标准

<!-- 每个功能需求对应的验收条件 -->
PRDEOF
        success "创建 $prd_dir/prd.md"
    fi

    success "创建 $prd_dir/verification/"
    echo ""
else
    info "Step 5: PRD 目录 — 跳过（未指定 --with-prd）"
    echo ""
fi

# ===== Step 6: 平台配置写入 =====
info "Step 6: 写入平台配置..."
echo ""

case "$PLATFORM" in
    claude)
        mkdir -p .claude
        settings_file=".claude/settings.local.json"
        if [[ -f "$settings_file" ]] && [[ "$FORCE" -eq 0 ]]; then
            info "$settings_file 已存在，追加 QGW 配置"
            # 使用 Python 合并配置（如可用）
            if [[ -n "$PYTHON_CMD" ]]; then
                "$PYTHON_CMD" -c "
import json, os
f = '$settings_file'
try:
    with open(f, 'r', encoding='utf-8') as fp:
        cfg = json.load(fp)
except (FileNotFoundError, json.JSONDecodeError):
    cfg = {}
if 'env' not in cfg:
    cfg['env'] = {}
cfg['env']['QGW_HOOK_MODE'] = 'strict'
cfg['env']['QGW_PLATFORM'] = '$PLATFORM'
with open(f, 'w', encoding='utf-8') as fp:
    json.dump(cfg, fp, indent=2, ensure_ascii=False)
"
                success "更新 $settings_file（合并 QGW env）"
            else
                warn "无 Python，跳过自动合并。请手动添加 QGW 配置到 $settings_file"
            fi
        else
            cat > "$settings_file" << CLAUDEEOF
{
  "env": {
    "QGW_HOOK_MODE": "strict",
    "QGW_PLATFORM": "$PLATFORM"
  },
  "permissions": {
    "allow": [
      "Bash(bash */quality-gate-workflow/scripts/*)",
      "Bash(python */quality-gate-workflow/scripts/*)"
    ]
  }
}
CLAUDEEOF
            success "创建 $settings_file"
        fi
        ;;
    codex|general)
        agents_file="AGENTS.md"
        if [[ -f "$agents_file" ]] && [[ "$FORCE" -eq 0 ]]; then
            # 追加 QGW 配置段落
            if ! grep -q "quality-gate-workflow" "$agents_file" 2>/dev/null; then
                cat >> "$agents_file" << AGENTSEOF

## QGW 质量门禁

- 平台: $PLATFORM
- 模式: $MODE
- 触发: \`--gate1\` / \`--gate2\` / \`--all\` / \`--self\`
- 配置: \`.qgw/config.json\`
AGENTSEOF
                success "追加 QGW 配置到 $agents_file"
            else
                info "$agents_file 已含 QGW 配置，跳过"
            fi
        else
            cat > "$agents_file" << AGENTSEOF
# Project Agents Configuration

## QGW 质量门禁

- 平台: $PLATFORM
- 模式: $MODE
- 触发: \`--gate1\` / \`--gate2\` / \`--all\` / \`--self\`
- 配置: \`.qgw/config.json\`
- 文档目录: \`docs/plans/\` \`docs/verification/\` \`docs/reports/\` \`docs/sessions/\`

## 快速开始

\`\`\`bash
# Gate 1: 需求 → Plan
--gate1

# Gate 2: Plan → 代码
--gate2

# 全流程
--all
\`\`\`
AGENTSEOF
            success "创建 $agents_file"
        fi
        ;;
    opencode)
        plugin_file="opencode.config.qgw.json"
        cat > "$plugin_file" << OCEOF
{
  "plugins": {
    "quality-dev-skills": {
      "platform": "$PLATFORM",
      "mode": "$MODE",
      "hooks": { "mode": "strict" },
      "paths": {
        "config": ".qgw/config.json",
        "constitution": ".qgw/constitution.md"
      }
    }
  }
}
OCEOF
        success "创建 $plugin_file"
        ;;
    mimo)
        plugin_file=".mimo/qgw-plugin.json"
        mkdir -p .mimo
        cat > "$plugin_file" << MIMOEOF
{
  "name": "quality-dev-skills",
  "platform": "$PLATFORM",
  "mode": "$MODE",
  "hooks": { "mode": "strict" },
  "config": ".qgw/config.json",
  "constitution": ".qgw/constitution.md"
}
MIMOEOF
        success "创建 $plugin_file"
        ;;
esac

echo ""

# ===== Step 7: 初始化摘要 =====
info "Step 7: 初始化摘要"
echo ""

echo "========================================="
echo -e " ${GREEN}QGW 初始化完成${NC}"
echo "========================================="
echo "  平台:     $PLATFORM"
echo "  模式:     $MODE"
echo "  PRD:      ${PRD_NAME:-未创建}"
echo ""
echo "  已创建:"

# 检查各项是否存在
[[ -d ".qgw" ]]               && echo "    ✅ .qgw/"
[[ -f ".qgw/config.json" ]]   && echo "    ✅ .qgw/config.json"
[[ -f ".qgw/constitution.md" ]] && echo "    ✅ .qgw/constitution.md"
[[ -d "docs/plans" ]]          && echo "    ✅ docs/plans/"
[[ -d "docs/verification" ]]   && echo "    ✅ docs/verification/"
[[ -d "docs/reports" ]]        && echo "    ✅ docs/reports/"
[[ -d "docs/sessions" ]]       && echo "    ✅ docs/sessions/"

if [[ -n "$PRD_NAME" ]]; then
    [[ -d "docs/prd/$PRD_NAME" ]] && echo "    ✅ docs/prd/$PRD_NAME/"
fi

# 平台配置文件
case "$PLATFORM" in
    claude)   [[ -f ".claude/settings.local.json" ]] && echo "    ✅ .claude/settings.local.json" ;;
    codex|general) [[ -f "AGENTS.md" ]] && echo "    ✅ AGENTS.md" ;;
    opencode) [[ -f "opencode.config.qgw.json" ]] && echo "    ✅ opencode.config.qgw.json" ;;
    mimo)     [[ -f ".mimo/qgw-plugin.json" ]] && echo "    ✅ .mimo/qgw-plugin.json" ;;
esac

echo ""
echo "  下一步:"
echo "    1. 编辑 .qgw/constitution.md 定义项目需求约束"
echo "    2. 运行 health-check 验证配置:"
echo "       bash ~/.agents/skills/quality-gate-workflow/scripts/health-check.sh"
echo "    3. 开始使用:"
echo "       --gate1    需求 → Plan"
echo "       --gate2    Plan → 代码"
echo "       --all      全流程"
echo "========================================="

exit 0
