#!/bin/bash
# update-project-skill.sh - 更新项目技能脚本
# 更新project-dev-rule到最新模板版本

set -e

# 默认值
PROJECT_ROOT=""
FORCE=false
VERBOSE=false

# 显示帮助
show_help() {
    echo "用法: $0 [选项] [项目路径]"
    echo ""
    echo "选项:"
    echo "  -f, --force                   强制更新（跳过确认）"
    echo "  -v, --verbose                 显示详细信息"
    echo "  -h, --help                    显示此帮助"
    echo ""
    echo "示例:"
    echo "  $0 /path/to/project"
    echo "  $0 --force /path/to/project"
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -*)
            echo "未知参数: $1"
            show_help
            exit 1
            ;;
        *)
            PROJECT_ROOT="$1"
            shift
            ;;
    esac
done

# 检查项目路径
if [ -z "$PROJECT_ROOT" ]; then
    PROJECT_ROOT="."
fi

if [ ! -d "$PROJECT_ROOT" ]; then
    echo "错误: 项目目录不存在: $PROJECT_ROOT"
    exit 1
fi

SKILL_DIR="$PROJECT_ROOT/.agents/skills/project-dev-rule"
TEMPLATE_DIR="$(dirname "$0")/../shared/project-dev-rule-template"

# 检查技能目录
if [ ! -d "$SKILL_DIR" ]; then
    echo "错误: project-dev-rule技能不存在: $SKILL_DIR"
    echo "请先生成project-dev-rule技能"
    exit 1
fi

# 读取当前版本
if [ -f "$SKILL_DIR/SKILL.md" ]; then
    CURRENT_VERSION=$(grep "template_version:" "$SKILL_DIR/SKILL.md" | head -1 | cut -d: -f2 | tr -d ' ')
else
    CURRENT_VERSION="unknown"
fi

# 读取最新版本
if [ -f "$(dirname "$0")/../version.json" ]; then
    LATEST_VERSION=$(grep -o '"version": *"[^"]*"' "$(dirname "$0")/../version.json" | head -1 | cut -d'"' -f4)
else
    LATEST_VERSION="unknown"
fi

echo "当前版本: $CURRENT_VERSION"
echo "最新版本: $LATEST_VERSION"

# 检查是否需要更新
if [ "$CURRENT_VERSION" = "$LATEST_VERSION" ]; then
    echo "✅ 已是最新版本，无需更新"
    exit 0
fi

# 版本兼容性检查
if [ -f "$(dirname "$0")/check-compatibility.sh" ]; then
    if ! bash "$(dirname "$0")/check-compatibility.sh" -t "$LATEST_VERSION" -p "$CURRENT_VERSION"; then
        echo "❌ 版本不兼容，无法更新"
        exit 1
    fi
fi

# 确认更新
if [ "$FORCE" = false ]; then
    echo ""
    read -p "是否更新到版本 $LATEST_VERSION？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消更新"
        exit 0
    fi
fi

# 备份当前技能
BACKUP_DIR="$SKILL_DIR.backup.$(date +%Y%m%d%H%M%S)"
echo "备份当前技能到: $BACKUP_DIR"
cp -r "$SKILL_DIR" "$BACKUP_DIR"

# 更新技能
echo "更新project-dev-rule..."

# 更新版本信息
if [ -f "$SKILL_DIR/SKILL.md" ]; then
    sed -i "s/template_version: .*/template_version: $LATEST_VERSION/" "$SKILL_DIR/SKILL.md"
    sed -i "s/last_optimized: .*/last_optimized: $(date +%Y-%m-%d)/" "$SKILL_DIR/SKILL.md"
fi

# 更新hooks
if [ -d "$TEMPLATE_DIR/hooks" ]; then
    cp -r "$TEMPLATE_DIR/hooks/"* "$SKILL_DIR/hooks/" 2>/dev/null || mkdir -p "$SKILL_DIR/hooks" && cp -r "$TEMPLATE_DIR/hooks/"* "$SKILL_DIR/hooks/"
fi

# 记录日志
LOG_FILE="$PROJECT_ROOT/.project-skill.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
echo "$TIMESTAMP: updated from $CURRENT_VERSION to $LATEST_VERSION" >> "$LOG_FILE"

echo ""
echo "✅ 更新完成"
echo "   版本: $CURRENT_VERSION → $LATEST_VERSION"
echo "   备份: $BACKUP_DIR"
echo ""
echo "下一步:"
echo "  1. 检查 $SKILL_DIR/SKILL.md 是否正常"
echo "  2. 运行 quality-gate-workflow 测试"
