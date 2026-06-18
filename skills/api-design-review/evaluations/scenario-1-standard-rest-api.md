# Scenario 1: 标准 REST API 通过审查

## 触发条件

用户执行 `--api-review` 并提供符合规范的 OpenAPI spec。

## 输入

```json
{
  "paths": {
    "/api/v1/users": {
      "get": {
        "responses": {"200": {"description": "OK"}},
        "parameters": [{"name": "page", "in": "query"}, {"name": "page_size", "in": "query"}]
      },
      "post": {
        "responses": {"201": {"description": "Created"}, "400": {"description": "Bad Request"}}
      }
    },
    "/api/v1/users/{id}": {
      "get": {
        "responses": {"200": {"description": "OK"}, "404": {"description": "Not Found"}}
      },
      "patch": {
        "responses": {"200": {"description": "OK"}, "422": {"description": "Unprocessable"}}
      },
      "delete": {
        "responses": {"204": {"description": "No Content"}, "404": {"description": "Not Found"}}
      }
    }
  }
}
```

## 期望行为

- `check-api-convention.py` 退出码为 0 (PASS)
- 无 ERROR 输出
- 所有 URL 段为 kebab-case，无动词

## 验证标准

- [x] 复数名词命名通过
- [x] HTTP 方法语义正确
- [x] 201/204 响应码存在
- [x] 分页参数使用 page + page_size
