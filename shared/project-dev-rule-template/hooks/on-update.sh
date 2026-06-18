#!/bin/bash
# on-update.sh - 模板更新触发hooks
# 当模板版本更新时触发

set -e

PROJECT_ROOT=$1
TEMPLATE_VERSION=${2:-"1.0.0"}
SKILL_DIR="$PROJECT_ROOT/.agents/skills/project-dev-rule"
LOG_FILE="$PROJECT_ROOT/.project-skill.log"

echo "[hooks:on-update] 检查模板更新..."

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

# 3. 读取当前版本
if [ -f "$SKILL_DIR/SKILL.md" ]; then
  CURRENT_VERSION=$(grep "template_version:" "$SKILL_DIR/SKILL.md" | head -1 | cut -d: -f2 | tr -d ' ')
else
  CURRENT_VERSION="unknown"
fi

echo "当前模板版本: $CURRENT_VERSION"
echo "最新模板版本: $TEMPLATE_VERSION"

# 4. 比较版本
if [ "$CURRENT_VERSION" = "$TEMPLATE_VERSION" ]; then
  echo "✅ 已是最新版本"
  exit 0
fi

# 5. 版本兼容性检查
CURRENT_MAJOR=$(echo $CURRENT_VERSION | cut -d. -f1)
TEMPLATE_MAJOR=$(echo $TEMPLATE_VERSION | cut -d. -f1)

if [ "$TEMPLATE_MAJOR" -gt "$CURRENT_MAJOR" ] 2>/dev/null; then
  echo "⚠️  主版本升级，可能有不兼容变更"
  echo "建议查看迁移指南: ~/quality-dev-skills/docs/migration-guide.md"
fi

# 6. 生成迁移建议
echo ""
echo "模板从 $CURRENT_VERSION 更新到 $TEMPLATE_VERSION"
echo ""
echo "更新选项:"
echo "  1. 自动更新（推荐）"
echo "     在项目空间启动AI会话，执行:"
echo "     '更新project-dev-rule到模板版本 $TEMPLATE_VERSION'"
echo ""
echo "  2. 手动更新"
echo "     cd $PROJECT_ROOT"
echo "     bash ~/quality-dev-skills/scripts/update-project-skill.sh"
echo ""
echo "  3. 暂不更新"
echo "     当前技能仍可使用，但可能缺少新功能"

# 7. 记录日志
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
echo "$TIMESTAMP: template update check from $CURRENT_VERSION to $TEMPLATE_VERSION" >> "$LOG_FILE"

# 8. 询问用户（可选）
if [ -t 0 ]; then
  echo ""
  read -p "是否现在更新？(y/n) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "请在项目空间启动AI会话执行更新"
  fi
fi
