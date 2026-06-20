# Scenario 4: 空 OpenAPI Spec

## 触发条件

用户执行 `--api-review` 并提供一个 paths 为空的 OpenAPI spec。

## 输入

```json
{
  "openapi": "3.0.0",
  "paths": {}
}
```

## 期望行为

- `check-api-convention.py` 输出 "WARN: No paths found in spec"
- 退出码为 0（无 ERROR）
- 不输出任何 `[ERROR]` 行

## 验证标准

- [x] 退出码为 0
- [x] 输出包含 "No paths" 警告
- [x] 无 ERROR 级别输出
