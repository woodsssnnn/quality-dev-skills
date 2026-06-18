#!/bin/bash
# on-create.sh - 新项目初始化hooks
# 当project-dev-rule首次生成时触发

set -e

PROJECT_ROOT=$1
SKILL_DIR="$PROJECT_ROOT/.agents/skills/project-dev-rule"
LOG_FILE="$PROJECT_ROOT/.project-skill.log"

echo "[hooks:on-create] 初始化project-dev-rule..."

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

# 4. 检查SKILL.md是否已填写
if grep -q "\[AI根据项目上下文" "$SKILL_DIR/SKILL.md"; then
  echo "⚠️  SKILL.md 包含占位符，请先完成内容生成"
  exit 1
fi

# 5. 运行skill-optimizer评分（如果可用）
if [ -f ~/quality-dev-skills/scripts/evaluate.py ]; then
  echo "运行skill-optimizer评分..."
  cd ~/quality-dev-skills
  python3 scripts/evaluate.py --target "$SKILL_DIR" 2>/dev/null || echo "⚠️  评分失败，跳过"
fi

# 6. 验证CLAUDE.md绑定
if [ -f "$PROJECT_ROOT/CLAUDE.md" ]; then
  if grep -q "project-dev-rule" "$PROJECT_ROOT/CLAUDE.md"; then
    echo "✅ CLAUDE.md 已绑定project-dev-rule"
  else
    echo "⚠️  CLAUDE.md 未绑定project-dev-rule"
    echo "建议在CLAUDE.md中添加:"
    echo "  ## 项目开发规范"
    echo "  - 技能位置：\`.agents/skills/project-dev-rule/\`"
  fi
else
  echo "⚠️  CLAUDE.md 不存在"
fi

# 7. 记录日志
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
echo "$TIMESTAMP: project-dev-rule created at $SKILL_DIR" >> "$LOG_FILE"

# 8. 输出结果
echo ""
echo "✅ project-dev-rule 初始化完成"
echo "   技能位置: $SKILL_DIR"
echo "   日志文件: $LOG_FILE"
echo ""
echo "下一步:"
echo "  1. 检查 $SKILL_DIR/SKILL.md 是否完整"
echo "  2. 确认 CLAUDE.md 已绑定"
echo "  3. 运行 quality-gate-workflow 测试"
