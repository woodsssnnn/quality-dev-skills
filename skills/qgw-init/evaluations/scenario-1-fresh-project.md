# Scenario 1: 全新项目完整引导

## 触发条件

用户执行 `--init` 且项目目录中不存在 `.qgw/` 目录。

## 输入

```
--init
```

项目状态：全新项目，只有 `package.json` 和 `src/` 目录。

## 期望行为

1. 引导流程按 7 步顺序执行
2. Step 1: 检测到项目类型（前端/后端/全栈）并建议 workflow mode
3. Step 2: 用户确认 workflow mode（full/lite/ultra）
4. Step 3: 创建 `.qgw/` 目录结构
5. Step 4: 生成 `.qgw/config.json`（含平台、mode、version）
6. Step 5: 创建 `docs/` 目录（plans/reports/sessions/verification）
7. Step 6: 运行 `health-check.sh`，所有检查项通过
8. Step 7: 输出初始化摘要（成功 + 后续使用建议）

## 验证标准

- [ ] `.qgw/` 目录被创建
- [ ] `.qgw/config.json` 包含有效 JSON 且字段完整
- [ ] `docs/` 下 4 个子目录全部存在
- [ ] `health-check.sh` 退出码为 0
- [ ] 初始化摘要包含 `--gate1` 使用提示
