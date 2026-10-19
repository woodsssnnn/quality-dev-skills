#!/usr/bin/env python3
"""create-domain-pack.py — 从模板生成领域包骨架

在当前目录下创建 <name>/（复制 domains/_template/ 并替换占位 id）。
生成后即可被 governance 运行时加载（示例规则可立即跑通）。

用法（在期望创建位置的父目录执行）：
    python scripts/create-domain-pack.py <name>

约束：name 须为 kebab-case（^[a-z][a-z0-9]*(-[a-z0-9]+)*$），目标目录
必须不存在（不覆盖）。
依赖：仅 stdlib。
"""

import re
import shutil
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
TEMPLATE_ID = "my-pack"
REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "domains" / "_template"


def main() -> int:
    if len(sys.argv) != 2 or not NAME_RE.match(sys.argv[1]):
        print("用法: python scripts/create-domain-pack.py <kebab-case-name>", file=sys.stderr)
        print("示例: python scripts/create-domain-pack.py acme-stack", file=sys.stderr)
        return 2
    name = sys.argv[1]
    dst = Path.cwd() / name
    if dst.exists():
        print(f"错误：目标已存在（不覆盖）: {dst}", file=sys.stderr)
        return 2
    if not TEMPLATE_DIR.is_dir():
        print(f"错误：模板目录不存在: {TEMPLATE_DIR}", file=sys.stderr)
        return 2

    shutil.copytree(TEMPLATE_DIR, dst)

    # 替换占位 id（pack.json 的 id/name 与文档中的示例名）
    for f in [dst / "pack.json", dst / "README.md", dst / "governance.json",
              dst / "rules" / "example.json"]:
        if not f.is_file():
            continue
        text = f.read_text(encoding="utf-8")
        text = text.replace(TEMPLATE_ID, name).replace("我的领域包（改为你的人类可读名称）", name)
        f.write_text(text, encoding="utf-8")

    print(f"✅ 已生成领域包骨架: {dst}")
    print("后续：")
    print(f"  1. 编辑 {name}/pack.json 与 rules/example.json 为你的领域规则")
    print(f"  2. 校验：python scripts/validate-domain-pack.py <该包目录>")
    print(f"  3. 使用：项目 .qgw/governance.json 声明 \"packs\": [\"{name}\"]")
    print(f"     （或把包复制到项目 .qgw/packs/{name}/ 私有使用）")
    print(f"  4. 贡献：放入本仓库 domains/{name}/ 并提 PR（见 CONTRIBUTING.md）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
