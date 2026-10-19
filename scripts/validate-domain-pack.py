#!/usr/bin/env python3
"""validate-domain-pack.py — 领域包结构校验（本地与 CI 共用）

校验一个领域包目录是否符合 shared/domain-pack-spec.md：
  1. pack.json 必需且字段合法（schemaVersion/id/version/compatibility）
  2. rules/*.json 至少一个（_template 除外——模板本身即示例）；规则集
     schema 校验（id/appliesTo.extensions/rules[].id/severity/pattern|script）
  3. governance.json 若存在必须可解析且不含未知顶层键
  4. 脚本规则引用的 script 必须存在于包内
  5. 包内任何文件不得包含来源项目品牌词（中立性红线，模式运行时拼装）

用法：
    python scripts/validate-domain-pack.py <pack-dir>

退出码：0=通过 1=校验失败 2=用法错误
依赖：仅 stdlib。
"""

import json
import re
import sys
from pathlib import Path

KNOWN_CFG_KEYS = {"$comment", "promptMessages", "verifyCommands", "bashHints", "hints", "packs", "projectMarkers"}
SEVERITIES = {"block", "warn"}
PACK_ID_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+")
V4_RE = re.compile(r"^\d+\.\d+\.\d+\.\d+$")
# 禁词模式运行时拼装，避免本文件自身命中
_BANNED = ("e" + "pros", "je" + "cn")


def fail(msg, errors):
    errors.append(msg)


def validate_rule_set(path: Path, errors, pack_dir: Path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        fail(f"规则集不可解析: {path.name}: {e}", errors)
        return
    if not isinstance(data.get("id"), str) or not data["id"]:
        fail(f"{path.name}: 缺 id", errors)
    exts = data.get("appliesTo", {}).get("extensions")
    if not isinstance(exts, list) or not exts or not all(
            isinstance(x, str) and x.startswith(".") for x in exts):
        fail(f"{path.name}: appliesTo.extensions 应为非空的 '.ext' 列表", errors)
    rules = data.get("rules")
    if not isinstance(rules, list) or not rules:
        fail(f"{path.name}: rules 应为非空列表", errors)
        return
    ids = set()
    for i, r in enumerate(rules):
        rid = r.get("id")
        if not isinstance(rid, str) or not rid:
            fail(f"{path.name}: rules[{i}] 缺 id", errors)
            continue
        if rid in ids:
            fail(f"{path.name}: 规则 id 重复 {rid}", errors)
        ids.add(rid)
        if r.get("severity") not in SEVERITIES:
            fail(f"{path.name}: {rid} severity 必须是 block|warn", errors)
        has_pattern = isinstance(r.get("pattern"), str) and r["pattern"]
        has_script = isinstance(r.get("script"), str) and r["script"]
        if not has_pattern and not has_script:
            fail(f"{path.name}: {rid} 需要 pattern 或 script 之一", errors)
        if has_pattern:
            try:
                re.compile(r["pattern"], 0)
            except re.error as e:
                fail(f"{path.name}: {rid} 正则非法: {e}", errors)
        if has_script:
            sp = r["script"]
            if Path(sp).is_absolute() or ".." in sp.split("/"):
                fail(f"{path.name}: {rid} script 路径非法（须为包内相对路径）", errors)
            elif not (pack_dir / sp).is_file():
                fail(f"{path.name}: {rid} 引用的脚本不存在: {sp}", errors)
        if not isinstance(r.get("message"), str) or len(r.get("message", "")) < 8:
            fail(f"{path.name}: {rid} message 缺失或过短（须写清修复路径）", errors)


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: python scripts/validate-domain-pack.py <pack-dir>", file=sys.stderr)
        return 2
    pack_dir = Path(sys.argv[1])
    if not pack_dir.is_dir():
        print(f"错误：目录不存在 {pack_dir}", file=sys.stderr)
        return 2

    errors = []
    is_template = pack_dir.name == "_template"

    # 1. pack.json
    pack_meta = {}
    pj = pack_dir / "pack.json"
    try:
        pack_meta = json.loads(pj.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        fail(f"pack.json 缺失或不可解析: {e}", errors)
    if pack_meta:
        if pack_meta.get("schemaVersion") != 1:
            fail("pack.json schemaVersion 必须为 1", errors)
        pid = pack_meta.get("id", "")
        if not PACK_ID_RE.match(pid or ""):
            fail(f"pack.json id 非法（kebab-case）: {pid!r}", errors)
        elif pid != pack_dir.name and not is_template:
            fail(f"pack.json id ({pid}) 应与目录名 ({pack_dir.name}) 一致", errors)
        if not SEMVER_RE.match(pack_meta.get("version", "")):
            fail("pack.json version 应为 SemVer", errors)
        compat = pack_meta.get("compatibility", {})
        for k in ("minRuntime", "maxRuntime"):
            if not V4_RE.match(compat.get(k, "")):
                fail(f"pack.json compatibility.{k} 应为 4 级版本号", errors)

    # 2. rules/
    rules_dir = pack_dir / "rules"
    rule_files = sorted(rules_dir.glob("*.json")) if rules_dir.is_dir() else []
    if not rule_files and not is_template:
        fail("缺少 rules/*.json（领域包的核心价值；至少一个规则集）", errors)
    for rf in rule_files:
        validate_rule_set(rf, errors, pack_dir)

    # 3. governance.json
    gj = pack_dir / "governance.json"
    if gj.is_file():
        try:
            cfg = json.loads(gj.read_text(encoding="utf-8"))
            unknown = set(cfg.keys()) - KNOWN_CFG_KEYS
            if unknown:
                fail(f"governance.json 含未知顶层键: {sorted(unknown)}", errors)
            if "packs" in cfg:
                fail("governance.json 不应声明 packs（那是项目层字段）", errors)
        except (json.JSONDecodeError, OSError) as e:
            fail(f"governance.json 不可解析: {e}", errors)

    # 4. 中立性红线（包内全部文本文件）
    for f in sorted(pack_dir.rglob("*")):
        if not f.is_file() or f.suffix.lower() in {".png", ".jpg", ".ico"}:
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        for word in _BANNED:
            if word in text:
                fail(f"中立性红线：{f.relative_to(pack_dir)} 含来源项目品牌词", errors)

    if errors:
        print(f"✗ {pack_dir.name} 校验失败（{len(errors)} 项）：")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"✓ {pack_dir.name} 校验通过"
          + (f"（{len(rule_files)} 规则集）" if rule_files else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
