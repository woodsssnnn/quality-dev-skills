#!/bin/bash
# on-optimize.sh - 优化触发hooks
# 当发现规范不适用或需要优化时触发

set -e

PROJECT_ROOT=$1
SKILL_DIR="$PROJECT_ROOT/.agents/skills/project-dev-rule"
LOG_FILE="$PROJECT_ROOT/.project-skill.log"

echo "[hooks:on-optimize] 优化project-dev-rule..."

# 1. 验证项目目录
if [ ! -d "$PROJECT_ROOT" ]; then
  echo "❌ 项目目录不存在: $PROJECT_ROOT"
  exit 1
fi

# 2. 验证技能目录
if [ ! -d "$SKILL_DIR" ]; then
  echo "❌ 技能目录不存在: $SKILL_DIR"
  echo "请先生成project-dev-rule技能"
  exit 1
fi

# 3. 验证SKILL.md
if [ ! -f "$SKILL_DIR/SKILL.md" ]; then
  echo "❌ SKILL.md 不存在: $SKILL_DIR/SKILL.md"
  exit 1
fi

# 4. 运行skill-optimizer（如果可用）
if [ -f ~/quality-dev-skills/scripts/optimize.py ]; then
  echo "运行skill-optimizer优化..."
  cd ~/quality-dev-skills
  python3 scripts/optimize.py --target "$SKILL_DIR" 2>/dev/null
  OPTIMIZE_RESULT=$?
  
  if [ $OPTIMIZE_RESULT -eq 0 ]; then
    echo "✅ skill-optimizer优化完成"
  else
    echo "⚠️  skill-optimizer优化失败，使用手动优化"
  fi
else
  echo "⚠️  skill-optimizer不可用，使用手动优化"
fi

# 5. 生成优化建议
echo ""
echo "优化建议:"
echo ""
echo "  1. 内容优化"
echo "     - 检查SKILL.md中的规范是否过时"
echo "     - 更新代码示例"
echo "     - 补充缺失的规范"
echo ""
echo "  2. 结构优化"
echo "     - 检查references/目录是否完整"
echo "     - 更新验证清单"
echo "     - 补充常见错误"
echo ""
echo "  3. 触发词优化"
echo "     - 更新description中的触发词"
echo "     - 补充遗漏的场景"

# 6. 记录日志
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
echo "$TIMESTAMP: optimization triggered" >> "$LOG_FILE"

# 7. 输出下一步
echo ""
echo "下一步:"
echo "  1. 在项目空间启动AI会话"
echo "  2. 描述需要优化的问题"
echo "  3. AI会根据反馈更新SKILL.md"
echo ""
echo "示例:"
echo "  'project-dev-rule中的组件规范不适用于我们的项目，需要更新'"
