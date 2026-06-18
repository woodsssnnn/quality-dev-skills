# Scenario 3: 响应码与错误格式问题

## 触发条件

用户执行 `--api-review` 并提供响应定义不规范的 OpenAPI spec。

## 输入

```json
{
  "paths": {
    "/api/v1/orders": {
      "post": {
        "responses": {
          "200": {"description": "OK"}
        }
      }
    },
    "/api/v1/orders/{id}": {
      "delete": {
        "responses": {
          "200": {"description": "OK"}
        }
      }
    },
    "/api/v1/products": {
      "get": {
        "responses": {
          "200": {"description": "OK"},
          "400": {
            "description": "Bad Request",
            "content": {
              "application/json": {
                "schema": {
                  "properties": {
                    "error": {
                      "properties": {
                        "msg": {"type": "string"}
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

## 期望行为

- `check-api-convention.py` 退出码为 2 (WARN)
- 检测出以下 WARN：
  - POST `/api/v1/orders` 缺少 201 响应
  - DELETE `/api/v1/orders/{id}` 缺少 204 响应
  - GET `/api/v1/products` 400 错误响应缺少 `code` + `message` 字段（只有 `msg`）

## 验证标准

- [x] POST 缺少 201 被检测
- [x] DELETE 缺少 204 被检测
- [x] 错误响应格式问题被检测
- [x] 退出码为 2（WARN 级别，非 FAIL）
