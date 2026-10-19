#!/usr/bin/env python3
"""build-zcode-plugin.py — 构建 ZCode 自包含插件市场（dist/）

ZCode 安装插件时会把插件目录拷贝进缓存：插件内引用外部相对路径的声明
（如 skills: "../../skills/"）在缓存副本中会失效。本脚本把仓库内容组装成
自包含插件 + 市场清单，供 `/plugin marketplace add <repo>/dist` 安装。

产出（dist/ 已 gitignore）：
    dist/marketplace.json          市场清单（两个插件条目）
    dist/zcode-quality-skills/     技能插件：.zcode-plugin/plugin.json + skills/
    dist/zcode-governance/         治理运行时插件：hooks/ + agents/（自包含拷贝）

用法：
    python scripts/build-zcode-plugin.py [--clean]

依赖：仅 stdlib。
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST = REPO_ROOT / "dist"
SKILLS_PLUGIN_DIR = DIST / "zcode-quality-skills"
GOV_PLUGIN_DIR = DIST / "zcode-governance"

# 拷贝时排除的垃圾/运行时产物
EXCLUDE_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".DS_Store", ".git"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".log"}


def copy_tree(src: Path, dst: Path):
    def ignore(directory, names):
        dropped = set()
        for n in names:
            if n in EXCLUDE_NAMES:
                dropped.add(n)
        return dropped

    shutil.copytree(src, dst, ignore=ignore)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def skill_ids():
    out = []
    if (REPO_ROOT / "skills").is_dir():
        for d in sorted((REPO_ROOT / "skills").iterdir()):
            if d.is_dir() and (d / "SKILL.md").is_file():
                out.append(d.name)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="构建 ZCode 自包含插件市场")
    parser.add_argument("--clean", action="store_true", help="构建前清空 dist/")
    args = parser.parse_args()

    if not (REPO_ROOT / "skills").is_dir():
        print("错误：仓库结构异常（缺少 skills/）", file=sys.stderr)
        return 2

    if args.clean and DIST.exists():
        shutil.rmtree(DIST)
    if DIST.exists():
        print("错误：dist/ 已存在（避免误覆盖，请先 --clean）", file=sys.stderr)
        return 2
    DIST.mkdir(parents=True)

    # 1. 技能插件（自包含 skills/ 副本）
    skills = skill_ids()
    if not skills:
        print("错误：skills/ 下未发现任何技能", file=sys.stderr)
        return 2
    copy_tree(REPO_ROOT / "skills", SKILLS_PLUGIN_DIR / "skills")
    write_json(SKILLS_PLUGIN_DIR / ".zcode-plugin" / "plugin.json", {
        "name": "quality-dev-skills",
        "version": "0.9.0.0",
        "description": f"质量门禁技能集（{len(skills)} 技能：{'、'.join(skills)}）——"
                       "流程级质量门禁/技能优化/PRD 解析/初始化引导。",
        "author": {"name": "quality-dev-skills"},
        "license": "MIT",
        "skills": "skills",
    })

    # 2. 治理运行时插件（governance/ 本身自包含，整树拷贝）
    copy_tree(REPO_ROOT / "governance", GOV_PLUGIN_DIR)

    # 3. 市场清单
    write_json(DIST / "marketplace.json", {
        "name": "quality-dev-skills-marketplace",
        "description": "通用质量与治理技能市场（自包含构建产物）",
        "owner": {"name": "quality-dev-skills"},
        "plugins": [
            {
                "name": "quality-dev-skills",
                "description": "流程级质量门禁技能集（PRD→Plan→Verifier + 技能优化 + PRD 解析 + 初始化引导）",
                "author": {"name": "quality-dev-skills"},
                "source": "./zcode-quality-skills",
                "category": "development",
            },
            {
                "name": "governance",
                "description": "代码级治理运行时：声明式规则门禁 + 验证机器凭证 + 哈希链事件流 + 完整性自保护",
                "author": {"name": "quality-dev-skills"},
                "source": "./zcode-governance",
                "category": "development",
            },
        ],
    })

    # 汇总
    file_count = sum(1 for p in DIST.rglob("*") if p.is_file())
    print(f"✅ 构建完成: {DIST}")
    print(f"   技能插件: {len(skills)} 技能 → zcode-quality-skills/")
    print(f"   治理插件: zcode-governance/（hooks + agents）")
    print(f"   共 {file_count} 文件")
    print("")
    print("安装：在 ZCode 中执行")
    print(f"  /plugin marketplace add {DIST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
