# Scenario 2: URL 命名违规检测

## 触发条件

用户执行 `--api-review` 并提供包含命名违规的 OpenAPI spec。

## 输入

```json
{
  "paths": {
    "/api/v1/getUsers": {
      "get": {
        "responses": {"200": {"description": "OK"}}
      }
    },
    "/api/v1/user_profile": {
      "get": {
        "responses": {"200": {"description": "OK"}}
      }
    },
    "/api/v1/OrderItems/": {
      "get": {
        "responses": {"200": {"description": "OK"}}
      }
    }
  }
}
```

## 期望行为

- `check-api-convention.py` 退出码为 1 (FAIL)
- 检测出以下 ERROR：
  - `/api/v1/getUsers`: 动词 "getUsers" + camelCase
  - `/api/v1/user_profile`: underscore 命名
  - `/api/v1/OrderItems/`: 大写开头 + 尾斜杠

## 验证标准

- [x] 检测到动词 URL 段
- [x] 检测到 camelCase
- [x] 检测到 underscore
- [x] 检测到尾斜杠
- [x] 退出码为 1
