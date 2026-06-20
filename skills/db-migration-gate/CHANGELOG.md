# Changelog

All notable changes to db-migration-gate will be documented in this file.

## [0.8.2.0] - 2026-06-20

### Added
- pytest 测试套件：13 用例（文件名 3 + DROP 操作 3 + down 脚本 2 + TRUNCATE 2 + 边缘场景 3）
- Eval 场景新增：scenario-4（空迁移目录）和 scenario-5（多重危险操作混合）
- `pytest.ini` + `tests/conftest.py` 测试基础设施

---

## [0.8.0.1] - 2026-06-19

### Changed
- 版本号跟随项目升级至 0.8.0.1

---

## [0.8.0.0] - 2026-06-18

### Added
- 初始发布：数据库迁移质量门禁
- 3 个评估场景（safe-migration / dangerous-drop / mixed-ddl-dml）
- `check-migration-safety.py` 自动化检查脚本
- `migration-conventions.md` 参考规范文档
- `manifest-entry.json` 技能清单条目
- 支持 `--db-migration` 参数触发 + `--strict` 严格模式
