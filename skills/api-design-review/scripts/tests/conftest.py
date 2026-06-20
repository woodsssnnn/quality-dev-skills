"""
conftest.py — pytest fixtures for check-api-convention.py tests.

使用 importlib 加载含连字符的模块。
每个测试函数前重置全局 ISSUES 列表。
"""

import importlib.util
import sys
from pathlib import Path

import pytest

# ── 加载 check-api-convention.py ──────────────────────────────────────────────
_SCRIPT_PATH = Path(__file__).parent.parent / "check-api-convention.py"

spec = importlib.util.spec_from_file_location("check_api_convention", _SCRIPT_PATH)
check_api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_api)

sys.modules["check_api_convention"] = check_api

# 导出
check_url_naming = check_api.check_url_naming
check_http_methods = check_api.check_http_methods
check_responses = check_api.check_responses
check_pagination = check_api.check_pagination
analyze_spec = check_api.analyze_spec
ISSUES = check_api.ISSUES


@pytest.fixture(autouse=True)
def reset_issues():
    """每个测试前清空全局 ISSUES 列表，测试后恢复。"""
    original = ISSUES.copy()
    ISSUES.clear()
    yield
    ISSUES.clear()
    ISSUES.extend(original)


@pytest.fixture
def standard_spec():
    """返回一个符合规范的标准 OpenAPI spec。"""
    return {
        "paths": {
            "/api/v1/users": {
                "get": {
                    "responses": {"200": {"description": "OK"}},
                    "parameters": [
                        {"name": "page", "in": "query"},
                        {"name": "page_size", "in": "query"},
                    ],
                },
                "post": {
                    "responses": {
                        "201": {"description": "Created"},
                        "400": {"description": "Bad Request"},
                    }
                },
            },
            "/api/v1/users/{id}": {
                "get": {
                    "responses": {
                        "200": {"description": "OK"},
                        "404": {"description": "Not Found"},
                    }
                },
                "patch": {
                    "responses": {
                        "200": {"description": "OK"},
                        "422": {"description": "Unprocessable"},
                    }
                },
                "delete": {
                    "responses": {
                        "204": {"description": "No Content"},
                        "404": {"description": "Not Found"},
                    }
                },
            },
        }
    }
