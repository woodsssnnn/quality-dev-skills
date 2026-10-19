# 输出品牌规范（Output Brand Spec）v1

> 目标：所有经本仓库产出的**对话内可见输出**，在任何一个 agent 宿主里都有统一的
> 品牌识别度与产品化观感。通用层只用 GFM Markdown（表格/emoji/Unicode）——
> 这是在所有宿主（终端/网页/桌面）都稳定渲染的最大公约数。

## 品牌元素

### 1. 报头（多行输出的第一行）

```
> 🛡 QGW · <子域> · <标题> [<状态>]
```

- `🛡 QGW` 是主品牌（quality gate workflow / quality-dev-skills）
- `<子域>`：`governance`、`quality-gate-workflow`、`prd-parse`、`domains` 等
- `[<状态>]` 可选：`✅ 通过` / `❌ 失败` / `⚠️ 有警告`——单行结论已知时带上

示例：

```
> 🛡 QGW · governance · 事件流校验 [✅ 通过]
> 🛡 QGW · quality-gate-workflow · plan-completeness
```

### 2. 单行输出（轻量工具）

```
🛡 QGW · verify-links · ✅ 12 md / 34 内链全部通过
```

### 3. 语义 emoji（全局统一，不得混用）

| emoji | 含义 |
|-------|------|
| ✅ | 通过 / 成功 |
| 🟡 | 部分满足 / 未验证（可继续） |
| ❌ | 失败 / 不满足 |
| ⏭ | 跳过（增量未变更） |
| ⚠️ | 警告（不阻断） |
| 🔒 | 阻断（block 级违规） |
| 🧪 | 验证凭证相关 |
| 📊 | 统计/聚合输出 |

### 4. 进度条（10 格）

```
█████░░░░░ 5/9
```

`█` 已完成、`░` 未完成；行尾 `已完成/总数`。用于步骤进度与覆盖率。

### 5. 页脚（仅正式报告文件，不用于对话内轻量输出）

```
---
> 🛡 由 quality-dev-skills 生成 · 机器可复核（event-query --verify-last）
```

## 表格规范

- 状态列放第一列或最后一列，值用语义 emoji 开头（`✅ PASS`）
- 关键数字列右对齐语义（保持 GFM 默认即可，不追求对齐语法）

## 不适用范围（诚实边界）

1. **hook 的 stderr 单行**（Stop 轮统计等）：防死循环纪律要求单行、仅 stderr——
   用紧凑前缀 `[governance ▍统计]`，不上表格/多行
2. **exit-2 阻断消息**：信息密度优先（规则号/行号/修复路径必须醒目），
   仅保留既有 `[governance 门禁]` 前缀
3. **机器可读输出**（`--json` 等）：必须保持纯 JSON，禁止注入品牌行

## 落地清单（谁该遵守）

| 输出点 | 采用方式 |
|--------|----------|
| `governance/scripts/*`（event-query/distill-scope/verify-links/blast-radius/install-hooks） | 单行报头 |
| `governance/hooks/turn-stats.js` | 紧凑前缀 `[governance ▍统计]` |
| `scripts/check-banned-terms.sh`、`validate-domain-pack.py`、`create-domain-pack.py` | 单行报头 |
| `skills/quality-gate-workflow/scripts/report-generator.py` | 报头 + 页脚（generate_report 单点注入） |
| `skills/prd-parse/scripts/prd_parse.py` | 非 --json 模式单行报头 |
| 新增技能/工具 | 遵守本规范（CONTRIBUTING 引用） |
