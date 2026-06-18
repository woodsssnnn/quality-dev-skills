#!/bin/bash
# health-check.sh — 质量门禁健康检查 + 工作空间初始化
#
# 用途：
#   bash health-check.sh                    # 健康检查
#   bash health-check.sh --init-workspace   # 初始化工作空间产出物目录
#
# 工作空间产出物目录结构：
#   docs/plans/          — 实现计划文档（验收清单追加在末尾）
#   docs/verification/   — 结构化验收数据（JSON Schema 格式）
#   docs/reports/        — 审计报告、验证报告、回归测试报告

# 从脚本自身位置推断技能根目录（兼容 Windows/macOS/Linux）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# 工作空间初始化模式
if [ "$1" = "--init-workspace" ]; then
    echo "========================================="
    echo " 质量门禁 — 工作空间初始化"
    echo "========================================="
    echo ""

    # 创建 docs/ 子目录
    for dir in plans verification reports sessions; do
        target="docs/$dir"
        if [ -d "$target" ]; then
            echo "  ✅ docs/$dir/ 已存在"
        else
            mkdir -p "$target"
            echo "  📁 创建 docs/$dir/"

            # 复制 README 模板（sessions 无模板）
            if [ "$dir" != "sessions" ]; then
                readme_src="$SKILL_DIR/assets/workspace-readmes/${dir}-README.md"
                if [ -f "$readme_src" ]; then
                    cp "$readme_src" "$target/_README.md"
                    echo "  📄 写入 docs/$dir/_README.md"
                fi
            fi
        fi
    done

    echo ""
    echo "工作空间产出物目录已就绪："
    echo "  docs/plans/          ← 实现计划文档"
    echo "  docs/verification/   ← 验收数据（JSON）"
    echo "  docs/reports/        ← 审计/验证报告"
    echo "  docs/sessions/       ← 会话摘要（v6.0）"
    echo ""
    echo "下一步："
    echo "  1. 在项目 CLAUDE.md 中添加触发词配置"
    echo "  2. 声明 gate2_dev_rules（如需要）"
    exit 0
fi

# ===== 健康检查模式 =====
PASS=0
FAIL=0
WARN=0

echo "========================================="
echo " 质量门禁 (quality-gate-workflow) 健康检查"
echo "========================================="
echo ""

# 1. 技能文件存在性
echo "[1/12] 技能文件..."
if [ -f "$SKILL_DIR/SKILL.md" ]; then
    version=$(grep 'version:' "$SKILL_DIR/SKILL.md" | head -1 | sed 's/.*: *"\(.*\)".*/\1/')
    echo "  ✅ SKILL.md 存在 (v$version)"
    PASS=$((PASS+1))
else
    echo "  ❌ SKILL.md 不存在"
    FAIL=$((FAIL+1))
fi

# 2. 参考文件完整性
echo ""
echo "[2/12] 参考文件..."
for f in acceptance-criteria-schema.json error-patterns.json regression-test-cases.md verifier-templates.md constitution-template.md; do
    if [ -f "$SKILL_DIR/references/$f" ]; then
        echo "  ✅ references/$f"
        PASS=$((PASS+1))
    else
        echo "  ❌ references/$f 缺失"
        FAIL=$((FAIL+1))
    fi
done

# 3. 脚本完整性
echo ""
echo "[3/12] 脚本文件..."
for f in verify-checkpoint.sh health-check.sh; do
    if [ -f "$SKILL_DIR/scripts/$f" ]; then
        echo "  ✅ scripts/$f"
        PASS=$((PASS+1))
    else
        echo "  ❌ scripts/$f 缺失"
        FAIL=$((FAIL+1))
    fi
done

# 4. 工作空间产出物目录
echo ""
echo "[4/12] 工作空间产出物目录..."
for dir in plans verification reports sessions; do
    if [ -d "docs/$dir" ]; then
        echo "  ✅ docs/$dir/"
        PASS=$((PASS+1))
    else
        echo "  ❌ docs/$dir/ 不存在 — 运行 --init-workspace 创建"
        FAIL=$((FAIL+1))
    fi
done

# 5. 项目 CLAUDE.md 触发词
echo ""
echo "[5/12] 项目 CLAUDE.md 触发词..."
if [ -f "CLAUDE.md" ]; then
    if grep -q "quality-gate-workflow" "CLAUDE.md" 2>/dev/null; then
        echo "  ✅ quality-gate-workflow 触发词已配置"
        PASS=$((PASS+1))
    elif grep -q "prd-checkpoint-guard\|plan-checkpoint-guard" "CLAUDE.md" 2>/dev/null; then
        echo "  ⚠️  检测到旧版触发词 (prd-checkpoint-guard / plan-checkpoint-guard)"
        echo "     建议更新为 quality-gate-workflow v3.0"
        WARN=$((WARN+1))
    else
        echo "  ❌ 未找到 quality-gate-workflow 触发词"
        echo "     请在 CLAUDE.md 中添加触发词配置"
        FAIL=$((FAIL+1))
    fi
else
    echo "  ⚠️  当前目录没有 CLAUDE.md"
    WARN=$((WARN+1))
fi

# 6. dev_rule 配置检查
echo ""
echo "[6/12] dev_rule 配置..."
if [ -f "CLAUDE.md" ]; then
    # 优先检查 dev_rule_path（新方式）
    if grep -q "dev_rule_path" "CLAUDE.md" 2>/dev/null; then
        dev_rule_path=$(grep -oP 'dev_rule_path[：:]\s*`?[^`\n]+`?' "CLAUDE.md" | head -1 | sed 's/dev_rule_path[：:]\s*`//;s/`$//')
        echo "  已声明 dev_rule_path: $dev_rule_path"
        
        # 验证路径是否存在
        if [ -d "$dev_rule_path" ] || [ -f "$dev_rule_path/SKILL.md" ]; then
            echo "  ✅ dev_rule_path 存在"
            PASS=$((PASS+1))
        else
            echo "  ❌ dev_rule_path 不存在: $dev_rule_path"
            FAIL=$((FAIL+1))
        fi
    # 兼容旧方式：检查 gate_dev_rules
    elif grep -q "gate_dev_rules\|gate2_dev_rules\|Gate 项目 dev rules\|Gate 2 项目 dev rules" "CLAUDE.md" 2>/dev/null; then
        # 从反引号中提取技能名称
        dev_rules_line=$(grep -E "Gate (项目|2 项目) dev rules" "CLAUDE.md")
        dev_rules=$(echo "$dev_rules_line" | grep -oE '`[^`]+`' | sed 's/`//g' | tr '\n' ' ')
        echo "  已声明 (兼容模式): $dev_rules"
        echo "  ⚠️  建议迁移到 dev_rule_path 配置"
        # 验证每个声明的技能文件是否存在
        dev_rules_clean=$(echo "$dev_rules" | sed 's/、/ /g' | sed 's/,/ /g')
        all_exist=1
        for skill in $dev_rules_clean; do
            # 跳过非技能名称的词（如中文说明）
            case "$skill" in
                *-dev-rule|*-skill|*-rule|project-*|quality-*)
                    if [ -f "$HOME/.claude/skills/$skill/SKILL.md" ] || [ -f ".claude/skills/$skill/SKILL.md" ]; then
                        echo "  ✅ $skill — 文件存在"
                    else
                        echo "  ❌ $skill — 文件不存在！verifier 将跳过此规范"
                        all_exist=0
                        FAIL=$((FAIL+1))
                    fi
                    ;;
            esac
        done
        if [ "$all_exist" -eq 1 ]; then
            PASS=$((PASS+1))
        fi
    else
        echo "  ⚠️  未声明 dev_rule（Gate 1/2 将使用通用规范）"
        WARN=$((WARN+1))
    fi
fi

# 7. gate1_constitution 检查
echo ""
echo "[7/12] gate1_constitution 配置..."
if [ -f "CLAUDE.md" ]; then
    if grep -q "gate1_constitution\|Gate 1 项目 constitution" "CLAUDE.md" 2>/dev/null; then
        echo "  ✅ 已声明项目级需求解析约束"
        PASS=$((PASS+1))
    else
        echo "  ℹ️  未声明 gate1_constitution（可选，模板见 references/constitution-template.md）"
        WARN=$((WARN+1))
    fi
fi

# 8. Hook 配置检查
echo ""
echo "[8/12] Hook 配置..."
hook_configured=0
for settings_file in ".claude/settings.json" ".claude/settings.local.json" "$HOME/.claude/settings.json"; do
    if [ -f "$settings_file" ] && grep -q "verify-checkpoint" "$settings_file" 2>/dev/null; then
        echo "  ✅ verify-checkpoint.sh Hook 已配置 ($settings_file)"
        hook_configured=1
        PASS=$((PASS+1))
        break
    fi
done
if [ "$hook_configured" -eq 0 ]; then
    echo "  ℹ️  verify-checkpoint.sh Hook 未配置（可选，用于提交前强制检查）"
    echo "     配置方式见 scripts/verify-checkpoint.sh 头部注释"
    WARN=$((WARN+1))
fi

# 9. QGW-INDEX.md（v6.0）
echo ""
echo "[9/12] QGW-INDEX.md..."
if [ -f "docs/QGW-INDEX.md" ]; then
    echo "  ✅ docs/QGW-INDEX.md 存在"
    PASS=$((PASS+1))
else
    echo "  ℹ️  docs/QGW-INDEX.md 尚未创建（首次 Gate 1 P0 后自动生成）"
    WARN=$((WARN+1))
fi

# 10. Hook 模式检查（v6.0）
echo ""
echo "[10/12] Hook 模式..."
hook_mode_found=0
for settings_file in ".claude/settings.json" ".claude/settings.local.json" "$HOME/.claude/settings.json"; do
    if [ -f "$settings_file" ] && grep -q "QGW_HOOK_MODE" "$settings_file" 2>/dev/null; then
        hook_mode=$(grep "QGW_HOOK_MODE" "$settings_file" | head -1 | sed 's/.*: *"\(.*\)".*/\1/')
        echo "  ✅ QGW_HOOK_MODE=$hook_mode ($settings_file)"
        hook_mode_found=1
        PASS=$((PASS+1))
        break
    fi
done
if [ "$hook_mode_found" -eq 0 ]; then
    echo "  ℹ️  QGW_HOOK_MODE 未设置（默认 strict）"
    echo "     可通过 hook-install.sh --mode=strict|warn|off 设置"
    WARN=$((WARN+1))
fi

# 11. 数据库 MCP 可用性
echo ""
echo "[11/12] 数据库 MCP..."
db_mcp_found=0
for settings_file in ".claude/settings.json" ".claude/settings.local.json" "$HOME/.claude/settings.json"; do
    if [ -f "$settings_file" ] && grep -q "test-db-mcp\|mysql_query" "$settings_file" 2>/dev/null; then
        echo "  ✅ DB MCP 配置已找到 ($settings_file)"
        echo "     提示：Gate 1 P1.5 和 Gate 2 S3.5 将使用数据库验证"
        db_mcp_found=1
        PASS=$((PASS+1))
        break
    fi
done
if [ "$db_mcp_found" -eq 0 ]; then
    echo "  ⚠️  未检测到 DB MCP (test-db-mcp) 配置"
    echo "     后端 Gate 1 数据库调查和 Gate 2 Schema 验证将降级为仅静态分析"
    echo "     建议配置 test-db-mcp 或 local-db-mcp 以获得数据库事实验证能力"
    WARN=$((WARN+1))
fi

# 12. 工作空间层 error-patterns
echo ""
echo "[12/12] 工作空间层自进化数据..."
if [ -f "docs/verification/error-patterns.json" ]; then
    pattern_count=$(grep -c '"id"' "docs/verification/error-patterns.json" 2>/dev/null || echo "0")
    echo "  ✅ docs/verification/error-patterns.json 存在 ($pattern_count 个模式)"
    PASS=$((PASS+1))
else
    echo "  ℹ️  docs/verification/error-patterns.json 尚未创建（首次 FAIL 后自动生成）"
    WARN=$((WARN+1))
fi

# 汇总
echo ""
echo "========================================="
echo " 汇总: ✅ $PASS 通过  ❌ $FAIL 失败  ⚠️  $WARN 警告"
echo "========================================="

if [ "$FAIL" -gt 0 ]; then
    echo " ⚠ 有 $FAIL 项检查失败，请修复后再使用。"
    echo " 运行 --init-workspace 可自动创建缺失的工作空间目录。"
    exit 1
else
    echo " 🎉 质量门禁已就绪。"
    exit 0
fi
