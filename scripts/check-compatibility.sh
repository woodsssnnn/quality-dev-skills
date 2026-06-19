#!/bin/bash
# check-compatibility.sh - 版本兼容性检查脚本
# 检查模板版本与项目技能版本的兼容性

set -euo pipefail

# 默认值
TEMPLATE_VERSION=""
PROJECT_VERSION=""
VERBOSE=false

# 显示帮助
show_help() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -t, --template-version VERSION  模板版本号"
    echo "  -p, --project-version VERSION   项目技能版本号"
    echo "  -v, --verbose                   显示详细信息"
    echo "  -h, --help                      显示此帮助"
    echo ""
    echo "示例:"
    echo "  $0 -t 1.0.0 -p 1.0.0"
    echo "  $0 --template-version 2.0.0 --project-version 1.0.0"
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--template-version)
            TEMPLATE_VERSION="$2"
            shift 2
            ;;
        -p|--project-version)
            PROJECT_VERSION="$2"
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
        *)
            echo "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查必需参数
if [ -z "$TEMPLATE_VERSION" ] || [ -z "$PROJECT_VERSION" ]; then
    echo "错误: 必须指定模板版本和项目版本"
    show_help
    exit 1
fi

# 版本比较函数
version_compare() {
    local v1=$1
    local v2=$2
    
    # 分割版本号（支持 4 级: Major.Minor.Patch.Iteration）
    IFS='.' read -r v1_major v1_minor v1_patch v1_iter <<< "$v1"
    IFS='.' read -r v2_major v2_minor v2_patch v2_iter <<< "$v2"
    v1_iter=${v1_iter:-0}
    v2_iter=${v2_iter:-0}
    
    # 比较主版本号
    if [ "$v1_major" -gt "$v2_major" ]; then
        return 1
    elif [ "$v1_major" -lt "$v2_major" ]; then
        return -1
    fi
    
    # 比较次版本号
    if [ "$v1_minor" -gt "$v2_minor" ]; then
        return 1
    elif [ "$v1_minor" -lt "$v2_minor" ]; then
        return -1
    fi
    
    # 比较补丁版本号
    if [ "$v1_patch" -gt "$v2_patch" ]; then
        return 1
    elif [ "$v1_patch" -lt "$v2_patch" ]; then
        return -1
    fi
    
    # 比较迭代号（第 4 级）
    if [ "$v1_iter" -gt "$v2_iter" ]; then
        return 1
    elif [ "$v1_iter" -lt "$v2_iter" ]; then
        return -1
    fi
    
    return 0
}

# 读取兼容性配置
CONFIG_FILE="$(dirname "$0")/../version.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "错误: 找不到version.json配置文件"
    exit 1
fi

# 使用grep和sed解析JSON（简单实现）
MIN_PROJECT_VERSION=$(grep -o '"min_project_version": *"[^"]*"' "$CONFIG_FILE" | cut -d'"' -f4)
MAX_PROJECT_VERSION=$(grep -o '"max_project_version": *"[^"]*"' "$CONFIG_FILE" | cut -d'"' -f4)

if [ "$VERBOSE" = true ]; then
    echo "模板版本: $TEMPLATE_VERSION"
    echo "项目版本: $PROJECT_VERSION"
    echo "兼容范围: $MIN_PROJECT_VERSION - $MAX_PROJECT_VERSION"
    echo ""
fi

# 检查项目版本是否在兼容范围内
version_compare "$PROJECT_VERSION" "$MIN_PROJECT_VERSION"
MIN_RESULT=$?

version_compare "$PROJECT_VERSION" "$MAX_PROJECT_VERSION"
MAX_RESULT=$?

if [ $MIN_RESULT -lt 0 ]; then
    echo "❌ 不兼容: 项目版本 ($PROJECT_VERSION) 低于最低要求 ($MIN_PROJECT_VERSION)"
    echo "请升级项目技能到 $MIN_PROJECT_VERSION 或更高版本"
    exit 1
elif [ $MAX_RESULT -gt 0 ]; then
    echo "⚠️  警告: 项目版本 ($PROJECT_VERSION) 高于推荐最高版本 ($MAX_PROJECT_VERSION)"
    echo "可能需要更新模板以支持新版本"
fi

# 检查模板主版本是否兼容
TEMPLATE_MAJOR=$(echo $TEMPLATE_VERSION | cut -d. -f1)
PROJECT_MAJOR=$(echo $PROJECT_VERSION | cut -d. -f1)

if [ "$TEMPLATE_MAJOR" -gt "$PROJECT_MAJOR" ]; then
    echo "❌ 不兼容: 模板主版本 ($TEMPLATE_MAJOR) 高于项目主版本 ($PROJECT_MAJOR)"
    echo "请升级项目技能到主版本 $TEMPLATE_MAJOR 或更高版本"
    exit 1
fi

echo "✅ 版本兼容: 模板 $TEMPLATE_VERSION 与项目 $PROJECT_VERSION 兼容"
exit 0
