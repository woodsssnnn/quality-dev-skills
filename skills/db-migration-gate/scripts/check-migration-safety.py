#!/usr/bin/env python3
"""数据库迁移安全检查脚本 (stdlib only)。

Usage:
    python check-migration-safety.py <migration-dir>
    python check-migration-safety.py <migration-file>

检查项:
  1. DROP TABLE/COLUMN 需要 CONFIRM 标记
  2. 迁移文件必须有 down 脚本
  3. 索引命名约定 idx_{table}_{column}
  4. 迁移文件名包含时间戳
  5. 禁止 TRUNCATE TABLE
  6. 数据回填与 schema 变更分离

Exit codes: 0=PASS, 1=FAIL, 2=WARN
"""

import argparse
import re
import sys
from pathlib import Path


ISSUES = []


def issue(level: str, filepath: str, msg: str):
    ISSUES.append({"level": level, "file": filepath, "message": msg})
    print(f"[{level}] {filepath}: {msg}")


def check_filename_convention(filepath: Path):
    """检查迁移文件名是否包含时间戳。"""
    name = filepath.stem

    # Alembic: 20260618_1030_description
    alembic_pattern = re.compile(r"^\d{8}_\d{4}_")
    # Flyway: V202606181030__description
    flyway_pattern = re.compile(r"^V\d{12}__")

    if alembic_pattern.match(name) or flyway_pattern.match(name):
        return

    issue("ERROR", str(filepath.name), "Migration filename missing timestamp (expected YYYYMMDD_HHMM_ or V{timestamp}__)")


def check_drop_operations(filepath: Path, content: str):
    """检查 DROP 操作是否有 CONFIRM 标记。"""
    lines = content.splitlines()

    for i, line in enumerate(lines, 1):
        stripped = line.strip().upper()

        # Check DROP TABLE
        if re.search(r"\bDROP\s+TABLE\b", stripped) and "IF EXISTS" not in stripped:
            # Look for CONFIRM in nearby comments
            context = "\n".join(lines[max(0, i - 3):i + 1])
            if "CONFIRM" not in context.upper():
                issue("ERROR", f"{filepath.name}:{i}", "DROP TABLE without CONFIRM marker")

        # Check DROP COLUMN
        if re.search(r"\bDROP\s+(COLUMN|CONSTRAINT)\b", stripped):
            context = "\n".join(lines[max(0, i - 3):i + 1])
            if "CONFIRM" not in context.upper():
                issue("ERROR", f"{filepath.name}:{i}", f"DROP COLUMN/CONSTRAINT without CONFIRM marker")

        # Check TRUNCATE
        if re.search(r"\bTRUNCATE\b", stripped):
            issue("ERROR", f"{filepath.name}:{i}", "TRUNCATE TABLE is forbidden in migrations")


def check_down_script(filepath: Path, migration_dir: Path):
    """检查是否存在对应的 down 脚本。"""
    name = filepath.stem

    # Check for Alembic-style down in same file (upgrade/downgrade functions)
    content = filepath.read_text(encoding="utf-8", errors="ignore")
    if "def downgrade" in content or "def down" in content:
        return

    # Check for separate down file
    possible_down_names = [
        f"{name}_down.sql",
        f"{name}_down.py",
        name.replace("up", "down") + filepath.suffix,
    ]

    for down_name in possible_down_names:
        if (migration_dir / down_name).exists():
            return

    # Check for Flyway-style undo
    undo_pattern = re.compile(r"^U\d{12}__")
    if undo_pattern.match(name):
        return

    issue("ERROR", filepath.name, "No down/rollback script found for this migration")


def check_index_naming(filepath: Path, content: str):
    """检查索引命名是否符合 idx_{table}_{column} 格式。"""
    # Match CREATE INDEX statements
    index_pattern = re.compile(
        r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)",
        re.IGNORECASE,
    )

    for match in index_pattern.finditer(content):
        index_name = match.group(1)
        if not re.match(r"^(idx|uniq|pk|fk|ck)_\w+", index_name):
            issue("WARN", filepath.name, f"Index '{index_name}' doesn't follow naming convention (idx_/uniq_/pk_/fk_/ck_)")


def check_add_column_defaults(filepath: Path, content: str):
    """检查新增列是否有 DEFAULT 值或允许 NULL。"""
    add_col_pattern = re.compile(
        r"ADD\s+COLUMN\s+\w+\s+\w+(.*?)(?:;|$)",
        re.IGNORECASE | re.MULTILINE,
    )

    for match in add_col_pattern.finditer(content):
        col_def = match.group(1).upper()
        if "DEFAULT" not in col_def and "NOT NULL" in col_def and "NULL" not in col_def.replace("NOT NULL", ""):
            issue("WARN", filepath.name, "ADD COLUMN with NOT NULL but no DEFAULT value")


def check_data_backfill(content: str, filepath: Path):
    """检查是否有数据回填与 schema 变更混合。"""
    has_ddl = bool(re.search(r"\b(CREATE|ALTER|DROP)\s+TABLE\b", content, re.IGNORECASE))
    has_dml = bool(re.search(r"\b(UPDATE|INSERT\s+INTO)\b", content, re.IGNORECASE))

    if has_ddl and has_dml:
        issue("ERROR", filepath.name, "Schema change (DDL) and data backfill (DML) mixed in same migration")


def analyze_file(filepath: Path, migration_dir: Path):
    """分析单个迁移文件。"""
    check_filename_convention(filepath)

    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        issue("ERROR", filepath.name, f"Cannot read file: {e}")
        return

    check_drop_operations(filepath, content)
    check_down_script(filepath, migration_dir)
    check_index_naming(filepath, content)
    check_add_column_defaults(filepath, content)
    check_data_backfill(content, filepath)


def main():
    parser = argparse.ArgumentParser(description="Check database migration safety")
    parser.add_argument("target", help="Migration directory or file to check")
    args = parser.parse_args()

    target = Path(args.target)

    if target.is_file():
        migration_dir = target.parent
        files = [target]
    elif target.is_dir():
        migration_dir = target
        files = sorted(
            f for f in target.iterdir()
            if f.suffix in (".sql", ".py") and f.is_file()
        )
    else:
        print(f"ERROR: Target not found: {target}", file=sys.stderr)
        sys.exit(1)

    if not files:
        print("No migration files found.")
        sys.exit(0)

    print(f"Analyzing {len(files)} migration file(s)...\n")

    for f in files:
        analyze_file(f, migration_dir)

    # Summary
    errors = sum(1 for i in ISSUES if i["level"] == "ERROR")
    warns = sum(1 for i in ISSUES if i["level"] == "WARN")

    print(f"\n{'='*40}")
    print(f"Results: {errors} errors, {warns} warnings")

    if errors > 0:
        print("FAIL: Migration safety check failed")
        sys.exit(1)
    elif warns > 0:
        print("WARN: Issues found but no hard failures")
        sys.exit(2)
    else:
        print("PASS: All migration safety checks passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
