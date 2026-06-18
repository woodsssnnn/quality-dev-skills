# API 设计约定

REST API 设计规范，适用于所有对外和对内 API。

## URL 命名规则

### 资源路径

- 使用**复数名词**：`/users`, `/orders`, `/products`
- 使用 **kebab-case**：`/order-items`（非 `/orderItems` 或 `/order_items`）
- 嵌套资源最多两层：`/users/{id}/orders`（不推荐更深嵌套）
- 版本号放路径前缀：`/api/v1/users`

### 禁止

- URL 中使用动词：~~`/getUsers`~~ → `/users` (GET)
- URL 中使用大写字母
- 尾斜杠：~~`/users/`~~ → `/users`

## HTTP 方法使用

| 方法 | 用途 | 幂等 | 安全 |
|------|------|------|------|
| GET | 查询资源 | 是 | 是 |
| POST | 创建资源 | 否 | 否 |
| PUT | 全量替换 | 是 | 否 |
| PATCH | 部分更新 | 是 | 否 |
| DELETE | 删除资源 | 是 | 否 |

### 规则

- GET 请求**不得修改**服务端状态
- POST 创建成功返回 `201 Created` + `Location` 头
- DELETE 成功返回 `204 No Content`
- 批量操作使用 POST + 动作后缀：`POST /orders/{id}/cancel`

## HTTP 状态码

| 状态码 | 场景 |
|--------|------|
| 200 OK | GET 成功，PUT/PATCH 成功 |
| 201 Created | POST 创建成功 |
| 204 No Content | DELETE 成功，无响应体 |
| 400 Bad Request | 请求参数错误 |
| 401 Unauthorized | 未认证 |
| 403 Forbidden | 已认证但无权限 |
| 404 Not Found | 资源不存在 |
| 409 Conflict | 资源冲突（重复创建等） |
| 422 Unprocessable Entity | 参数校验失败 |
| 500 Internal Server Error | 服务端未知错误 |

### 禁止

- 所有错误都返回 200 + 自定义 code
- 使用 500 代替具体客户端错误码

## 响应格式

### 成功响应

```json
{
  "data": { ... },
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

### 错误响应

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "字段 'email' 格式无效",
    "details": [
      {"field": "email", "reason": "invalid_format"}
    ]
  }
}
```

## 分页

- 参数名：`page`（从 1 开始）+ `page_size`（默认 20，最大 100）
- 响应包含 `meta.page`, `meta.page_size`, `meta.total`
- 大数据集支持 cursor 分页：`?cursor=xxx&limit=20`

## OpenAPI 一致性

- 所有 API 必须有 OpenAPI 3.0 spec 文件
- spec 中的 path / method / schema 必须与实际路由一致
- 新增 endpoint 必须同步更新 spec
- CI 检查 spec 与路由定义的一致性
