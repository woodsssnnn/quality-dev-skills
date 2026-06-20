# Scenario 3: 非交互模式（--yes）

## 触发条件

用户执行 `--init --yes` 或通过 `qgw-init.sh --yes` 非交互模式运行。

## 输入

```
--init --yes
```

项目状态：全新项目，无 `.qgw/` 目录。

## 期望行为

1. 跳过所有交互式确认步骤
2. 使用默认值：workflow mode = full，平台 = 自动检测
3. 直接创建 `.qgw/` 目录和 `config.json`
4. 直接创建 `docs/` 目录结构
5. 运行 `health-check.sh`
6. 输出非交互式初始化摘要

## 验证标准

- [ ] 全程无用户交互提示
- [ ] `config.json` 中 mode 为 "full"
- [ ] `docs/` 下 4 个子目录全部存在
- [ ] `health-check.sh` 退出码为 0
- [ ] 输出包含 "non-interactive mode" 字样
