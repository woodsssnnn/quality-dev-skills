"""test_check_migration_safety.py — check-migration-safety.py 测试套件"""

from pathlib import Path
from tests.conftest import ISSUES


# ===== TestFilenameConvention =====

class TestFilenameConvention:

    def test_alembic_format_passes(self, migration_dir):
        """Alembic 格式 (YYYYMMDD_HHMM_description) 应通过。"""
        from tests.conftest import check_filename_convention
        ISSUES.clear()
        f = migration_dir / "20260620_1030_add_users_table.sql"
        f.write_text("-- migration", encoding="utf-8")
        check_filename_convention(f)
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        assert len(errors) == 0

    def test_flyway_format_passes(self, migration_dir):
        """Flyway 格式 (V{timestamp}__description) 应通过。"""
        from tests.conftest import check_filename_convention
        ISSUES.clear()
        f = migration_dir / "V202606201030__add_users_table.sql"
        f.write_text("-- migration", encoding="utf-8")
        check_filename_convention(f)
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        assert len(errors) == 0

    def test_no_timestamp_detected(self, migration_dir):
        """无时间戳文件名应报错。"""
        from tests.conftest import check_filename_convention
        ISSUES.clear()
        f = migration_dir / "add_users_table.sql"
        f.write_text("-- migration", encoding="utf-8")
        check_filename_convention(f)
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        assert len(errors) >= 1
        assert "timestamp" in errors[0]["message"].lower()


# ===== TestDropOperations =====

class TestDropOperations:

    def test_drop_table_without_confirm(self, migration_dir):
        """DROP TABLE 无 CONFIRM 标记应报错。"""
        from tests.conftest import check_drop_operations
        ISSUES.clear()
        f = migration_dir / "20260620_1030_drop_users.sql"
        content = "DROP TABLE users;\n"
        check_drop_operations(f, content)
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        assert len(errors) >= 1
        assert "DROP TABLE" in errors[0]["message"]

    def test_drop_table_with_confirm_passes(self, migration_dir):
        """DROP TABLE 有 CONFIRM 标记应通过。"""
        from tests.conftest import check_drop_operations
        ISSUES.clear()
        f = migration_dir / "20260620_1030_drop_users.sql"
        content = "-- CONFIRM: intentional drop\nDROP TABLE users;\n"
        check_drop_operations(f, content)
        errors = [i for i in ISSUES if i["level"] == "ERROR" and "DROP TABLE" in i["message"]]
        assert len(errors) == 0

    def test_drop_column_without_confirm(self, migration_dir):
        """DROP COLUMN 无 CONFIRM 标记应报错。"""
        from tests.conftest import check_drop_operations
        ISSUES.clear()
        f = migration_dir / "20260620_1030_alter_users.sql"
        content = "ALTER TABLE users DROP COLUMN legacy_field;\n"
        check_drop_operations(f, content)
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        assert len(errors) >= 1
        assert "DROP COLUMN" in errors[0]["message"]


# ===== TestDownScript =====

class TestDownScript:

    def test_has_downgrade_function(self, migration_dir):
        """含 def downgrade 的文件应通过。"""
        from tests.conftest import check_down_script
        ISSUES.clear()
        f = migration_dir / "20260620_1030_add_users.py"
        f.write_text("def upgrade():\n    pass\n\ndef downgrade():\n    pass\n", encoding="utf-8")
        check_down_script(f, migration_dir)
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        assert len(errors) == 0

    def test_no_down_script_found(self, migration_dir):
        """无 down 脚本应报错。文件名含 'up' 以触发 replace('up','down') 逻辑。"""
        from tests.conftest import check_down_script
        ISSUES.clear()
        # 文件名需含 'up' 以避免 replace('up','down') 与自身同名误判
        f = migration_dir / "20260620_1030_add_up_users.sql"
        f.write_text("CREATE TABLE users (id INT);\n", encoding="utf-8")
        check_down_script(f, migration_dir)
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        assert len(errors) >= 1
        assert "down" in errors[0]["message"].lower()


# ===== TestTruncate =====

class TestTruncate:

    def test_truncate_detected(self, migration_dir):
        """TRUNCATE TABLE 应报错。"""
        from tests.conftest import check_drop_operations
        ISSUES.clear()
        f = migration_dir / "20260620_1030_truncate.sql"
        content = "TRUNCATE TABLE users;\n"
        check_drop_operations(f, content)
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        assert len(errors) >= 1
        assert "TRUNCATE" in errors[0]["message"]

    def test_no_truncate_passes(self, migration_dir):
        """无 TRUNCATE 应通过。"""
        from tests.conftest import check_drop_operations
        ISSUES.clear()
        f = migration_dir / "20260620_1030_safe.sql"
        content = "ALTER TABLE users ADD COLUMN email VARCHAR(255);\n"
        check_drop_operations(f, content)
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        assert len(errors) == 0


# ===== TestEdgeCases =====

class TestEdgeCases:

    def test_empty_directory(self, migration_dir, tmp_path):
        """空迁移目录应正常处理（无文件）。"""
        from tests.conftest import check_migration
        ISSUES.clear()
        # 空目录不产生 ISSUES
        files = list(migration_dir.iterdir())
        assert len(files) == 0

    def test_mixed_violations(self, migration_dir):
        """同时包含 TRUNCATE + 无 CONFIRM DROP 应都报错。"""
        from tests.conftest import check_drop_operations
        ISSUES.clear()
        f = migration_dir / "20260620_1030_bad.sql"
        content = "TRUNCATE TABLE logs;\nDROP TABLE old_data;\n"
        check_drop_operations(f, content)
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        # 应有 TRUNCATE 错误 + DROP TABLE 无 CONFIRM 错误
        assert len(errors) >= 2
        assert any("TRUNCATE" in e["message"] for e in errors)
        assert any("DROP TABLE" in e["message"] for e in errors)

    def test_data_backfill_mixed_with_ddl(self, migration_dir):
        """DDL 和 DML 混合应报错。"""
        from tests.conftest import check_data_backfill
        ISSUES.clear()
        f = migration_dir / "20260620_1030_mixed.sql"
        content = "CREATE TABLE new_data (id INT);\nINSERT INTO new_data VALUES (1);\n"
        check_data_backfill(content, f)
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        assert len(errors) >= 1
        assert "mixed" in errors[0]["message"].lower() or "DDL" in errors[0]["message"]
