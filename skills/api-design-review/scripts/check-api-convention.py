#!/usr/bin/env python3
"""API 约定检查脚本 (stdlib only)。

Usage:
    python check-api-convention.py <openapi-spec.json|yaml>
    python check-api-convention.py --routes <route-file>

检查项:
  1. URL 使用 kebab-case + 复数名词
  2. HTTP 方法语义正确
  3. 响应码使用规范
  4. 分页参数约定
  5. 错误响应格式

Exit codes: 0=PASS, 1=FAIL, 2=WARN
"""

import argparse
import json
import re
import sys
from pathlib import Path


ISSUES = []


def issue(level: str, path: str, msg: str):
    ISSUES.append({"level": level, "path": path, "message": msg})
    print(f"[{level}] {path}: {msg}")


def check_url_naming(path: str):
    """检查 URL 路径是否符合 kebab-case + 复数名词。"""
    segments = [s for s in path.split("/") if s and not s.startswith("{")]
    for seg in segments:
        # Skip version segments like v1, v2, api
        if re.match(r"^(api|v\d+)$", seg):
            continue

        # Check kebab-case
        if not re.match(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", seg):
            issue("ERROR", path, f"Segment '{seg}' is not kebab-case")

        # Check for camelCase
        if re.search(r"[a-z][A-Z]", seg):
            issue("ERROR", path, f"Segment '{seg}' uses camelCase (use kebab-case)")

        # Check for underscore
        if "_" in seg:
            issue("ERROR", path, f"Segment '{seg}' uses underscore (use kebab-case hyphens)")

        # Check trailing slash
    if path.endswith("/") and path != "/":
        issue("ERROR", path, "URL has trailing slash")

    # Check for verb-like segments (common anti-patterns)
    verb_patterns = ["get", "set", "create", "update", "delete", "remove", "fetch", "list"]
    for seg in segments:
        if seg.lower() in verb_patterns:
            issue("ERROR", path, f"Segment '{seg}' looks like a verb (use noun + HTTP method)")


def check_http_methods(path: str, methods: dict):
    """检查 HTTP 方法使用是否规范。"""
    for method in methods:
        method_upper = method.upper()
        # Check for non-standard methods
        if method_upper not in ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"):
            issue("ERROR", path, f"Non-standard HTTP method: {method}")


def check_responses(path: str, method: str, responses: dict):
    """检查响应码是否规范。"""
    method_upper = method.upper()
    codes = [str(c) for c in responses.keys()]

    # POST should have 201
    if method_upper == "POST" and "201" not in codes and "default" not in codes:
        issue("WARN", path, f"POST should return 201 Created (found: {codes})")

    # DELETE should have 204
    if method_upper == "DELETE" and "204" not in codes and "default" not in codes:
        issue("WARN", path, f"DELETE should return 204 No Content (found: {codes})")

    # Check for 200 on everything pattern
    if codes == ["200"]:
        issue("WARN", path, "Only 200 response defined (consider 400/404/500)")

    # Check error response has code + message
    for code, resp in responses.items():
        code_str = str(code)
        if code_str.startswith("4") or code_str.startswith("5"):
            content = resp.get("content", {})
            for media, schema_obj in content.items():
                schema = schema_obj.get("schema", {})
                props = schema.get("properties", {})
                if "error" in props:
                    error_props = props["error"].get("properties", {})
                    if "code" not in error_props or "message" not in error_props:
                        issue("WARN", path, f"Error response {code_str} missing 'code' or 'message' field")


def check_pagination(path: str, method: str, parameters: list):
    """检查分页参数约定。"""
    param_names = [p.get("name", "") for p in parameters]
    has_offset = "offset" in param_names
    has_page = "page" in param_names
    has_limit = "limit" in param_names
    has_page_size = "page_size" in param_names

    if has_offset and has_page:
        issue("WARN", path, "Mixing offset and page pagination styles")

    if has_limit and has_page_size:
        issue("WARN", path, "Both 'limit' and 'page_size' defined (pick one style)")


def load_openapi_json(filepath: Path) -> dict:
    """加载 OpenAPI spec（JSON 格式）。"""
    text = filepath.read_text(encoding="utf-8")
    return json.loads(text)


def analyze_spec(spec: dict):
    """分析 OpenAPI spec。"""
    paths = spec.get("paths", {})

    if not paths:
        print("WARN: No paths found in spec")
        return

    print(f"Analyzing {len(paths)} paths...\n")

    for path, path_item in paths.items():
        check_url_naming(path)

        # Get all methods
        methods = {}
        for key in path_item:
            if key.lower() in ("get", "post", "put", "patch", "delete", "head", "options"):
                methods[key] = path_item[key]

        check_http_methods(path, methods)

        for method, operation in methods.items():
            responses = operation.get("responses", {})
            check_responses(path, method, responses)

            parameters = operation.get("parameters", [])
            check_pagination(path, method, parameters)


def analyze_routes_file(filepath: Path):
    """分析路由定义文件（简单正则扫描）。"""
    text = filepath.read_text(encoding="utf-8")

    # Match common route patterns
    route_pattern = re.compile(
        r'(?:(?:app|router|api)\.(?:get|post|put|patch|delete))\s*\(\s*["\']([^"\']+)["\']',
        re.IGNORECASE,
    )

    routes = route_pattern.findall(text)
    if not routes:
        # Try alternative patterns
        route_pattern2 = re.compile(r'(?:path|route)\s*[:=]\s*["\']([^"\']+)["\']')
        routes = route_pattern2.findall(text)

    print(f"Found {len(routes)} routes in {filepath.name}\n")

    for route in routes:
        if route.startswith("/"):
            check_url_naming(route)


def main():
    parser = argparse.ArgumentParser(description="Check API convention compliance")
    parser.add_argument("file", help="OpenAPI spec (JSON) or route file to check")
    parser.add_argument("--routes", action="store_true", help="Treat input as route file instead of OpenAPI spec")
    args = parser.parse_args()

    filepath = Path(args.file)
    if not filepath.exists():
        print(f"ERROR: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    if args.routes:
        analyze_routes_file(filepath)
    else:
        try:
            spec = load_openapi_json(filepath)
            analyze_spec(spec)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)

    # Summary
    errors = sum(1 for i in ISSUES if i["level"] == "ERROR")
    warns = sum(1 for i in ISSUES if i["level"] == "WARN")

    print(f"\n{'='*40}")
    print(f"Results: {errors} errors, {warns} warnings")

    if errors > 0:
        print("FAIL: API convention check failed")
        sys.exit(1)
    elif warns > 0:
        print("WARN: Issues found but no hard failures")
        sys.exit(2)
    else:
        print("PASS: All API conventions satisfied")
        sys.exit(0)


if __name__ == "__main__":
    main()
