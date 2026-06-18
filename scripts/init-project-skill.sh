#!/bin/bash
# init-project-skill.sh - 初始化项目技能脚本
# 在项目空间生成project-dev-rule技能

set -e

# 默认值
PROJECT_ROOT=""
TEMPLATE_VERSION=""
VERBOSE=false

# 显示帮助
show_help() {
    echo "用法: $0 [选项] [项目路径]"
    echo ""
    echo "选项:"
    echo "  -t, --template-version VERSION  指定模板版本"
    echo "  -v, --verbose                   显示详细信息"
    echo "  -h, --help                      显示此帮助"
    echo ""
    echo "示例:"
    echo "  $0 /path/to/project"
    echo "  $0 --template-version 1.0.0 /path/to/project"
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--template-version)
            TEMPLATE_VERSION="$2"
            shift 2
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

# 检查模板目录
if [ ! -d "$TEMPLATE_DIR" ]; then
    echo "错误: 模板目录不存在: $TEMPLATE_DIR"
    exit 1
fi

# 检查是否已存在
if [ -d "$SKILL_DIR" ]; then
    echo "⚠️  project-dev-rule技能已存在: $SKILL_DIR"
    read -p "是否覆盖？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消"
        exit 0
    fi
    rm -rf "$SKILL_DIR"
fi

# 获取版本号
if [ -z "$TEMPLATE_VERSION" ]; then
    if [ -f "$(dirname "$0")/../version.json" ]; then
        TEMPLATE_VERSION=$(grep -o '"version": *"[^"]*"' "$(dirname "$0")/../version.json" | head -1 | cut -d'"' -f4)
    else
        TEMPLATE_VERSION="1.0.0"
    fi
fi

echo "初始化project-dev-rule..."
echo "模板版本: $TEMPLATE_VERSION"

# 创建技能目录
mkdir -p "$SKILL_DIR"
mkdir -p "$SKILL_DIR/references/backend"
mkdir -p "$SKILL_DIR/references/frontend"
mkdir -p "$SKILL_DIR/references/business"
mkdir -p "$SKILL_DIR/scripts"
mkdir -p "$SKILL_DIR/hooks"

# 复制SKILL.md骨架
if [ -f "$TEMPLATE_DIR/structure/SKILL.md.skeleton" ]; then
    cp "$TEMPLATE_DIR/structure/SKILL.md.skeleton" "$SKILL_DIR/SKILL.md"
    
    # 替换占位符
    sed -i "s/{{GENERATED_AT}}/$(date +%Y-%m-%d)/" "$SKILL_DIR/SKILL.md"
    sed -i "s/{{TEMPLATE_VERSION}}/$TEMPLATE_VERSION/" "$SKILL_DIR/SKILL.md"
    sed -i "s/{{PROJECT_NAME}}/$(basename "$PROJECT_ROOT")/" "$SKILL_DIR/SKILL.md"
    
    echo "✅ SKILL.md 已生成"
fi

# 复制references占位文件
if [ -d "$TEMPLATE_DIR/structure/references" ]; then
    cp -r "$TEMPLATE_DIR/structure/references/"* "$SKILL_DIR/references/" 2>/dev/null || true
    echo "✅ references 目录已生成"
fi

# 复制hooks
if [ -d "$TEMPLATE_DIR/hooks" ]; then
    cp -r "$TEMPLATE_DIR/hooks/"* "$SKILL_DIR/hooks/" 2>/dev/null || true
    chmod +x "$SKILL_DIR/hooks/"*.sh 2>/dev/null || true
    echo "✅ hooks 目录已生成"
fi

# 创建CLAUDE.md绑定示例
CLAUDE_MD="$PROJECT_ROOT/CLAUDE.md.example"
if [ ! -f "$CLAUDE_MD" ]; then
    cat > "$CLAUDE_MD" << 'EOF'
# CLAUDE.md 示例

## 项目开发规范

- 技能位置：`.agents/skills/project-dev-rule/`
- 使用project-dev-rule作为开发规范

## Gate 配置

- dev_rule_path: .agents/skills/project-dev-rule

## 触发条件

- 当修改project-dev-rule时，触发on-update hooks
- 当发现规范不适用时，触发on-optimize hooks
EOF
    echo "✅ CLAUDE.md.example 已生成"
fi

# 记录日志
LOG_FILE="$PROJECT_ROOT/.project-skill.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
echo "$TIMESTAMP: initialized project-dev-rule v$TEMPLATE_VERSION" >> "$LOG_FILE"

echo ""
echo "✅ project-dev-rule 初始化完成"
echo "   技能位置: $SKILL_DIR"
echo "   模板版本: $TEMPLATE_VERSION"
echo ""
echo "下一步:"
echo "  1. 编辑 $SKILL_DIR/SKILL.md，填写项目特定内容"
echo "  2. 根据项目技术栈，参考 prompts/ 目录中的生成指南"
echo "  3. 更新 CLAUDE.md，添加 dev_rule_path 配置"
echo "  4. 运行 quality-gate-workflow 测试"
