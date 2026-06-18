#!/usr/bin/env python3
"""扫描 skills/ 目录自动生成 skill-manifest.json。

Usage:
    python scripts/generate-manifest.py              # 生成 manifest
    python scripts/generate-manifest.py --validate   # 验证 manifest 与实际一致

stdlib only — 不依赖任何第三方包。
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_VERSION = "0.8.0.0"
REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
MANIFEST_PATH = REPO_ROOT / "skill-manifest.json"
SCHEMA_PATH = REPO_ROOT / "shared" / "skill-manifest-schema.json"


def parse_yaml_frontmatter(skill_md: Path) -> dict:
    """解析 SKILL.md 的 YAML frontmatter（简单实现，不依赖 PyYAML）。"""
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    fm_text = text[3:end].strip()

    result = {}
    current_key = None
    current_list = None

    for line in fm_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # List item under current key
        if stripped.startswith("- ") and current_key and current_list is not None:
            val = stripped[2:].strip().strip("'\"")
            current_list.append(val)
            continue

        # Key-value pair
        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip().strip("'\"")

            # Handle nested keys like metadata.version
            if val == "" or val == "":
                # Start of a list or nested block
                current_key = key
                current_list = []
                result[key] = current_list
            else:
                current_key = key
                current_list = None
                result[key] = val

    # Flatten metadata dict
    if "metadata" in result and isinstance(result["metadata"], list):
        # metadata was detected as a list-start; re-parse
        pass
    # Re-parse for nested metadata.version
    meta = {}
    for line in fm_text.splitlines():
        m = re.match(r"^\s{2}(\w+)\s*:\s*(.+)$", line)
        if m:
            meta[m.group(1)] = m.group(2).strip().strip("'\"")
    if meta:
        result["metadata"] = meta

    return result


def detect_runtime_deps(skill_dir: Path) -> list:
    """扫描 scripts/ 目录检测运行时依赖。"""
    deps = []
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists():
        return deps

    for py_file in scripts_dir.glob("*.py"):
        deps.append("python>=3.8")
        break  # Only need one entry

    for sh_file in scripts_dir.glob("*.sh"):
        deps.append("bash")
        break

    return list(set(deps))


def count_references(skill_dir: Path) -> int:
    """统计 references/ 目录下的文件数。"""
    ref_dir = skill_dir / "references"
    if not ref_dir.exists():
        return 0
    return len([f for f in ref_dir.iterdir() if f.is_file()])


def detect_tools(skill_dir: Path) -> list:
    """根据目录内容推断所需的 Agent 工具。"""
    tools = ["Read"]
    if (skill_dir / "scripts").exists():
        tools.append("Bash")
    if (skill_dir / "references").exists():
        tools.append("Grep")
    return tools


def load_manifest_entry(skill_dir: Path) -> dict:
    """加载技能目录中的 manifest-entry.json（如果存在）。"""
    entry_path = skill_dir / "manifest-entry.json"
    if entry_path.exists():
        return json.loads(entry_path.read_text(encoding="utf-8"))
    return {}


def scan_skill(skill_dir: Path) -> dict:
    """扫描单个技能目录，生成 manifest entry。"""
    skill_id = skill_dir.name
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        return None

    fm = parse_yaml_frontmatter(skill_md)

    # Base entry from frontmatter
    version = "0.0.0.0"
    if "metadata" in fm and isinstance(fm["metadata"], dict):
        version = fm["metadata"].get("version", version)

    description = fm.get("description", f"{skill_id} skill")
    # Clean description - remove trigger hints for cleaner output
    if "Triggers on:" in description:
        description = description.split("Triggers on:")[0].strip().rstrip(".")

    entry = {
        "id": fm.get("name", skill_id),
        "version": version,
        "path": f"skills/{skill_id}",
        "description": description,
    }

    # Load override/supplement from manifest-entry.json
    manifest_entry = load_manifest_entry(skill_dir)
    if manifest_entry:
        for k, v in manifest_entry.items():
            if k != "id":  # Don't override id
                entry[k] = v

    # Auto-detect fields if not in manifest-entry
    if "category" not in entry:
        entry["category"] = "quality-assurance"

    if "dependencies" not in entry:
        runtime = detect_runtime_deps(skill_dir)
        tools = detect_tools(skill_dir)
        entry["dependencies"] = {
            "runtime": runtime,
            "skills": [],
            "tools": tools,
        }

    ref_count = count_references(skill_dir)
    if ref_count > 0 and "outputs" not in entry:
        entry["outputs"] = {
            "artifacts": [],
            "side_effects": [],
        }

    return entry


def generate_manifest() -> dict:
    """扫描所有技能目录，生成完整 manifest。"""
    skills = []

    if not SKILLS_DIR.exists():
        print(f"ERROR: skills directory not found: {SKILLS_DIR}", file=sys.stderr)
        sys.exit(1)

    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        entry = scan_skill(skill_dir)
        if entry:
            skills.append(entry)

    manifest = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator_version": SCRIPT_VERSION,
        "skills": skills,
    }

    return manifest


def validate_manifest(manifest: dict) -> list:
    """验证 manifest 与实际目录一致，返回错误列表。"""
    errors = []

    # Check each manifest entry has a corresponding directory
    for skill in manifest.get("skills", []):
        skill_path = REPO_ROOT / skill["path"]
        if not skill_path.exists():
            errors.append(f"Path not found: {skill['path']}")
            continue

        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            errors.append(f"SKILL.md not found in: {skill['path']}")
            continue

        # Verify version matches frontmatter
        fm = parse_yaml_frontmatter(skill_md)
        fm_version = "0.0.0.0"
        if "metadata" in fm and isinstance(fm["metadata"], dict):
            fm_version = fm["metadata"].get("version", fm_version)

        # Also check manifest-entry.json for version override
        me = load_manifest_entry(skill_path)
        me_version = me.get("version", fm_version)

        expected_version = me_version if me else fm_version
        if skill["version"] != expected_version:
            errors.append(
                f"Version mismatch for {skill['id']}: "
                f"manifest={skill['version']}, actual={expected_version}"
            )

    # Check for skills in directory not in manifest
    manifest_ids = {s["id"] for s in manifest.get("skills", [])}
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        if not (skill_dir / "SKILL.md").exists():
            continue
        fm = parse_yaml_frontmatter(skill_dir / "SKILL.md")
        name = fm.get("name", skill_dir.name)
        if name not in manifest_ids:
            errors.append(f"Skill not in manifest: {name} ({skill_dir.name})")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Generate or validate skill-manifest.json")
    parser.add_argument("--validate", action="store_true", help="Validate manifest against actual skills")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output path (default: skill-manifest.json)")
    args = parser.parse_args()

    if args.validate:
        if not MANIFEST_PATH.exists():
            print("ERROR: skill-manifest.json not found. Run without --validate first.", file=sys.stderr)
            sys.exit(1)

        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        errors = validate_manifest(manifest)

        if errors:
            print(f"Manifest validation FAILED ({len(errors)} errors):", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"Manifest OK: {len(manifest.get('skills', []))} skills validated.")
            sys.exit(0)
    else:
        manifest = generate_manifest()
        output_path = Path(args.output) if args.output else MANIFEST_PATH
        output_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Generated {output_path} with {len(manifest['skills'])} skills.")


if __name__ == "__main__":
    main()
