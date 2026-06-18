#!/bin/bash
# on-session-start.sh - 会话启动钩子
# 当AI会话启动时触发，检查project-dev-rule状态

set -e

PROJECT_ROOT=${1:-"."}
SKILL_DIR="$PROJECT_ROOT/.agents/skills/project-dev-rule"
LOG_FILE="$PROJECT_ROOT/.project-skill.log"

echo "[hooks:on-session-start] 检查project-dev-rule状态..."

# 1. 检查技能目录
if [ ! -d "$SKILL_DIR" ]; then
  echo "⚠️  project-dev-rule 未安装"
  echo "请先生成project-dev-rule技能"
  exit 0
fi

# 2. 检查SKILL.md
if [ ! -f "$SKILL_DIR/SKILL.md" ]; then
  echo "⚠️  SKILL.md 不存在"
  exit 0
fi

# 3. 读取强度级别
INTENSITY_LEVEL="full"  # 默认级别
if [ -f "$PROJECT_ROOT/CLAUDE.md" ]; then
  LEVEL=$(grep -oP '强度级别[：:]\s*\K\w+' "$PROJECT_ROOT/CLAUDE.md" 2>/dev/null | head -1)
  if [ -n "$LEVEL" ]; then
    INTENSITY_LEVEL="$LEVEL"
  fi
fi

# 4. 读取版本信息
VERSION=$(grep "template_version:" "$SKILL_DIR/SKILL.md" | head -1 | cut -d: -f2 | tr -d ' ')
GENERATED_AT=$(grep "generated_at:" "$SKILL_DIR/SKILL.md" | head -1 | cut -d: -f2 | tr -d ' ')

# 5. 输出状态
echo ""
echo "✅ project-dev-rule 已加载"
echo "   技能位置: $SKILL_DIR"
echo "   模板版本: $VERSION"
echo "   生成时间: $GENERATED_AT"
echo "   强度级别: $INTENSITY_LEVEL"
echo ""

# 6. 根据强度级别显示提示
case $INTENSITY_LEVEL in
  lite)
    echo "📌 Lite 模式：只检查核心规范，跳过可选检查"
    ;;
  full)
    echo "📌 Full 模式：检查所有规范，包括可选检查"
    ;;
  ultra)
    echo "📌 Ultra 模式：检查所有规范，严格零容忍"
    ;;
  off)
    echo "📌 Off 模式：跳过所有规范检查"
    ;;
  *)
    echo "⚠️  未知强度级别: $INTENSITY_LEVEL，使用默认 full"
    ;;
esac

# 7. 记录日志
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
echo "$TIMESTAMP: session started, intensity=$INTENSITY_LEVEL" >> "$LOG_FILE"
