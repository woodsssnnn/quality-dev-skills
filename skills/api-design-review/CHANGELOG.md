# Changelog

All notable changes to api-design-review will be documented in this file.

## [0.8.2.0] - 2026-06-20

### Added
- pytest 测试套件：17 用例（URL 命名 5 + HTTP 方法 3 + 响应码 4 + 分页 2 + 边缘场景 3）
- Eval 场景新增：scenario-4（空 OpenAPI spec）和 scenario-5（多类型混合违规）
- `pytest.ini` + `tests/conftest.py` 测试基础设施

---

## [0.8.0.1] - 2026-06-19

### Changed
- 版本号跟随项目升级至 0.8.0.1

---

## [0.8.0.0] - 2026-06-18

### Added
- 初始发布：REST API 设计审查门禁
- 3 个评估场景（standard-rest-api / url-naming-violations / response-code-issues）
- `check-api-convention.py` 自动化检查脚本
- `api-conventions.md` 参考规范文档
- `manifest-entry.json` 技能清单条目
- 支持 `--api-review` 参数触发 + `--routes` 路由模式
