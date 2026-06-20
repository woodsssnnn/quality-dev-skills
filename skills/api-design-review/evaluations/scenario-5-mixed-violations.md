# Scenario 5: 多类型混合违规

## 触发条件

用户执行 `--api-review` 并提供同时存在多种违规的 OpenAPI spec。

## 输入

```json
{
  "paths": {
    "/api/v1/getUsers": {
      "get": {
        "responses": {"200": {"description": "OK"}}
      }
    },
    "/api/v1/userProfiles": {
      "post": {
        "responses": {"200": {"description": "OK"}}
      }
    },
    "/api/v1/order_items": {
      "delete": {
        "responses": {"200": {"description": "OK"}}
      }
    }
  }
}
```

## 期望行为

- `check-api-convention.py` 退出码为 1（有 ERROR）
- 检测到以下违规：
  1. `/api/v1/getUsers` — 动词段 `getUsers` + camelCase
  2. `/api/v1/userProfiles` — camelCase 命名
  3. `/api/v1/order_items` — underscore 命名
  4. `GET /api/v1/getUsers` — 只有 200 响应
  5. `POST /api/v1/userProfiles` — 缺少 201 响应
  6. `DELETE /api/v1/order_items` — 缺少 204 响应

## 验证标准

- [x] 退出码为 1
- [x] 至少检测到 3 个 ERROR
- [x] 至少检测到 3 个 WARN
- [x] 所有违规路径均被标识
