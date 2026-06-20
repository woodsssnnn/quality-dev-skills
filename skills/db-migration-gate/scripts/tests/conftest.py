"""
conftest.py — pytest fixtures for check-migration-safety.py tests.

使用 importlib 加载含连字符的模块。
每个测试函数前重置全局 ISSUES 列表。
"""

import importlib.util
import sys
from pathlib import Path

import pytest

# ── 加载 check-migration-safety.py ────────────────────────────────────────────
_SCRIPT_PATH = Path(__file__).parent.parent / "check-migration-safety.py"

spec = importlib.util.spec_from_file_location("check_migration_safety", _SCRIPT_PATH)
check_migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_migration)

sys.modules["check_migration_safety"] = check_migration

# 导出
check_filename_convention = check_migration.check_filename_convention
check_drop_operations = check_migration.check_drop_operations
check_down_script = check_migration.check_down_script
check_index_naming = check_migration.check_index_naming
check_add_column_defaults = check_migration.check_add_column_defaults
check_data_backfill = check_migration.check_data_backfill
analyze_file = check_migration.analyze_file
ISSUES = check_migration.ISSUES


@pytest.fixture(autouse=True)
def reset_issues():
    """每个测试前清空全局 ISSUES 列表。"""
    original = ISSUES.copy()
    ISSUES.clear()
    yield
    ISSUES.clear()
    ISSUES.extend(original)


@pytest.fixture
def migration_dir(tmp_path):
    """创建临时迁移目录。"""
    d = tmp_path / "migrations"
    d.mkdir(parents=True, exist_ok=True)
    return d
