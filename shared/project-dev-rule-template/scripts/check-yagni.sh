#!/bin/bash
# check-yagni.sh - YAGNI检查脚本
# 检查代码是否符合YAGNI原则

set -e

# 默认值
TARGET_PATH=""
VERBOSE=false
FIX=false

# 显示帮助
show_help() {
    echo "用法: $0 [选项] [目标路径]"
    echo ""
    echo "选项:"
    echo "  -v, --verbose                   显示详细信息"
    echo "  -f, --fix                       自动修复（谨慎使用）"
    echo "  -h, --help                      显示此帮助"
    echo ""
    echo "示例:"
    echo "  $0 src/"
    echo "  $0 --verbose src/components/"
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -f|--fix)
            FIX=true
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
            TARGET_PATH="$1"
            shift
            ;;
    esac
done

# 检查目标路径
if [ -z "$TARGET_PATH" ]; then
    TARGET_PATH="."
fi

if [ ! -d "$TARGET_PATH" ] && [ ! -f "$TARGET_PATH" ]; then
    echo "错误: 目标路径不存在: $TARGET_PATH"
    exit 1
fi

echo "YAGNI 检查: $TARGET_PATH"
echo ""

# 计数器
TOTAL=0
YAGNI_COUNT=0

# 1. 检查不必要的依赖
echo "1. 检查不必要的依赖..."
if [ -f "package.json" ]; then
    # 检查是否有未使用的依赖
    DEPS=$(grep -oP '"[^"]+":\s*"[^"]*"' package.json | cut -d'"' -f2 | grep -v "name\|version\|description\|main\|scripts\|dependencies\|devDependencies")
    for dep in $DEPS; do
        TOTAL=$((TOTAL+1))
        # 检查是否在代码中使用
        if ! grep -r "$dep" src/ --include="*.js" --include="*.ts" --include="*.tsx" --include="*.jsx" > /dev/null 2>&1; then
            echo "  ⚠️  依赖 '$dep' 可能未使用"
            YAGNI_COUNT=$((YAGNI_COUNT+1))
        fi
    done
fi

# 2. 检查重复代码
echo "2. 检查重复代码..."
if command -v grep &> /dev/null; then
    # 简单的重复函数检测
    grep -rn "function " "$TARGET_PATH" --include="*.js" --include="*.ts" 2>/dev/null | \
        awk -F: '{print $3}' | \
        sort | uniq -d | \
        while read -r func; do
            TOTAL=$((TOTAL+1))
            echo "  ⚠️  函数 '$func' 可能重复定义"
            YAGNI_COUNT=$((YAGNI_COUNT+1))
        done
fi

# 3. 检查过度抽象
echo "3. 检查过度抽象..."
if [ -d "$TARGET_PATH" ]; then
    # 检查只有一个实现的接口/抽象类
    find "$TARGET_PATH" -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" | \
        while read -r file; do
            # 检查interface定义
            INTERFACES=$(grep -oP "interface\s+\w+" "$file" 2>/dev/null | awk '{print $2}')
            for interface in $INTERFACES; do
                TOTAL=$((TOTAL+1))
                # 检查实现数量
                IMPLEMENTATIONS=$(grep -r "implements\s*$interface" "$TARGET_PATH" 2>/dev/null | wc -l)
                if [ "$IMPLEMENTATIONS" -le 1 ]; then
                    echo "  ⚠️  接口 '$interface' 只有 $IMPLEMENTATIONS 个实现，可能过度抽象"
                    YAGNI_COUNT=$((YAGNI_COUNT+1))
                fi
            done
        done
fi

# 4. 检查不必要的配置
echo "4. 检查不必要的配置..."
if [ -f "tsconfig.json" ]; then
    # 检查是否有未使用的配置项
    TOTAL=$((TOTAL+1))
    if [ "$VERBOSE" = true ]; then
        echo "  ℹ️  tsconfig.json 存在，检查是否有未使用的配置"
    fi
fi

# 5. 检查样板代码
echo "5. 检查样板代码..."
if [ -d "$TARGET_PATH" ]; then
    # 检查空文件
    find "$TARGET_PATH" -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" | \
        while read -r file; do
            if [ ! -s "$file" ]; then
                TOTAL=$((TOTAL+1))
                echo "  ⚠️  空文件: $file"
                YAGNI_COUNT=$((YAGNI_COUNT+1))
            fi
        done
fi

# 输出结果
echo ""
echo "检查完成"
echo "  总检查项: $TOTAL"
echo "  YAGNI 发现: $YAGNI_COUNT"

if [ $YAGNI_COUNT -gt 0 ]; then
    echo ""
    echo "建议: 考虑简化代码，删除不必要的复杂度"
    exit 1
else
    echo ""
    echo "✅ 代码符合YAGNI原则"
    exit 0
fi
