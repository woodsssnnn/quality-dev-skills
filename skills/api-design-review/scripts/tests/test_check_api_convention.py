"""test_check_api_convention.py — check-api-convention.py 测试套件"""

from tests.conftest import ISSUES


# ===== TestUrlNaming =====

class TestUrlNaming:

    def test_kebab_case_passes(self):
        """kebab-case 路径应通过检查。"""
        check_url_naming = __import__("tests.conftest", fromlist=["check_url_naming"]).check_url_naming
        ISSUES.clear()
        check_url_naming("/api/v1/user-profiles")
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        assert len(errors) == 0

    def test_camel_case_detected(self):
        """camelCase 路径应报错。"""
        from tests.conftest import check_url_naming
        ISSUES.clear()
        check_url_naming("/api/v1/userProfiles")
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        assert len(errors) >= 1
        assert any("camelCase" in e["message"] for e in errors)

    def test_underscore_detected(self):
        """下划线命名应报错。"""
        from tests.conftest import check_url_naming
        ISSUES.clear()
        check_url_naming("/api/v1/user_profiles")
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        assert len(errors) >= 1
        assert any("underscore" in e["message"] for e in errors)

    def test_verb_detected(self):
        """动词段应报错。"""
        from tests.conftest import check_url_naming
        ISSUES.clear()
        check_url_naming("/api/v1/getUsers")
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        assert len(errors) >= 1

    def test_plural_noun_passes(self):
        """复数名词段应通过。"""
        from tests.conftest import check_url_naming
        ISSUES.clear()
        check_url_naming("/api/v1/orders")
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        assert len(errors) == 0


# ===== TestHttpMethods =====

class TestHttpMethods:

    def test_standard_methods_pass(self):
        """GET/POST/PATCH/DELETE 应通过。"""
        from tests.conftest import check_http_methods
        ISSUES.clear()
        check_http_methods("/api/v1/users", {"get": {}, "post": {}, "patch": {}, "delete": {}})
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        assert len(errors) == 0

    def test_non_standard_method_detected(self):
        """非标准方法应报错。"""
        from tests.conftest import check_http_methods
        ISSUES.clear()
        check_http_methods("/api/v1/users", {"PURGE": {}})
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        assert len(errors) >= 1
        assert "Non-standard" in errors[0]["message"]

    def test_options_method_passes(self):
        """OPTIONS 是合法方法。"""
        from tests.conftest import check_http_methods
        ISSUES.clear()
        check_http_methods("/api/v1/users", {"options": {}})
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        assert len(errors) == 0


# ===== TestResponseCodes =====

class TestResponseCodes:

    def test_post_without_201_warns(self):
        """POST 没有 201 响应应告警。"""
        from tests.conftest import check_responses
        ISSUES.clear()
        check_responses("/api/v1/users", "post", {"200": {"description": "OK"}})
        warns = [i for i in ISSUES if i["level"] == "WARN"]
        assert len(warns) >= 1
        assert "201" in warns[0]["message"]

    def test_delete_without_204_warns(self):
        """DELETE 没有 204 响应应告警。"""
        from tests.conftest import check_responses
        ISSUES.clear()
        check_responses("/api/v1/users/{id}", "delete", {"200": {"description": "OK"}})
        warns = [i for i in ISSUES if i["level"] == "WARN"]
        assert len(warns) >= 1
        assert "204" in warns[0]["message"]

    def test_only_200_warns(self):
        """只有 200 响应应告警（缺少错误响应）。"""
        from tests.conftest import check_responses
        ISSUES.clear()
        check_responses("/api/v1/users", "get", {"200": {"description": "OK"}})
        warns = [i for i in ISSUES if i["level"] == "WARN"]
        assert len(warns) >= 1
        assert "400" in warns[0]["message"] or "consider" in warns[0]["message"].lower()

    def test_post_with_201_passes(self):
        """POST 有 201 响应应通过。"""
        from tests.conftest import check_responses
        ISSUES.clear()
        check_responses("/api/v1/users", "post", {"201": {"description": "Created"}})
        warns = [i for i in ISSUES if i["level"] == "WARN" and "201" in i["message"]]
        assert len(warns) == 0


# ===== TestPagination =====

class TestPagination:

    def test_standard_pagination_passes(self):
        """page + page_size 参数应通过。"""
        from tests.conftest import check_pagination
        ISSUES.clear()
        params = [{"name": "page", "in": "query"}, {"name": "page_size", "in": "query"}]
        check_pagination("/api/v1/users", "get", params)
        warns = [i for i in ISSUES if i["level"] == "WARN"]
        assert len(warns) == 0

    def test_mixed_pagination_warns(self):
        """offset + page 混用应告警。"""
        from tests.conftest import check_pagination
        ISSUES.clear()
        params = [{"name": "offset", "in": "query"}, {"name": "page", "in": "query"}]
        check_pagination("/api/v1/users", "get", params)
        warns = [i for i in ISSUES if i["level"] == "WARN"]
        assert len(warns) >= 1


# ===== TestEdgeCases =====

class TestEdgeCases:

    def test_empty_paths(self, standard_spec):
        """空 paths 应输出 WARN 但不报错。"""
        from tests.conftest import analyze_spec
        ISSUES.clear()
        analyze_spec({"paths": {}})
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        assert len(errors) == 0

    def test_standard_spec_no_errors(self, standard_spec):
        """完整标准 spec 应无 ERROR。"""
        from tests.conftest import analyze_spec
        ISSUES.clear()
        analyze_spec(standard_spec)
        errors = [i for i in ISSUES if i["level"] == "ERROR"]
        assert len(errors) == 0

    def test_large_spec(self):
        """大量 endpoint（50个）应可正常处理。"""
        from tests.conftest import analyze_spec
        ISSUES.clear()
        paths = {f"/api/v1/resource-{i}": {"get": {"responses": {"200": {"description": "OK"}}}} for i in range(50)}
        analyze_spec({"paths": paths})
        # 不崩溃就是成功
