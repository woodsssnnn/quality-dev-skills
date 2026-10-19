# 场景 1：正常解析（HTML，零依赖后端）

## 输入

/tmp/prd-normal/需求说明.html：

```html
<!doctype html>
<html><head><meta charset="utf-8"><title>会员系统改版</title></head>
<body>
<h1>会员系统改版需求</h1>
<p>目标：提升会员活跃度，支持积分兑换。</p>
<h2>功能点</h2>
<ol><li>积分兑换商城</li><li>会员等级权益</li></ol>
<table>
  <tr><th>等级</th><th>折扣</th></tr>
  <tr><td>黄金</td><td>95 折</td></tr>
</table>
</body></html>
```

## 执行

```bash
python skills/prd-parse/scripts/prd_parse.py /tmp/prd-normal --json
```

## 期望

- exit code 0；manifest summary.ok=1（或 warning=1，无 failed）
- parsed/需求说明.md 含：`# 会员系统改版需求`（title 提升为 H1）、`## 功能点`、
  有序列表 `1. 积分兑换商城`、GFM 表格（`| 等级 | 折扣 |` + `| --- |`）
- text_chars > 0 且覆盖全部正文文字

# 场景 2：边界（扩展名与实际格式不符 + 增量跳过）

## 输入

/tmp/prd-edge/导出需求.docx —— 实际内容是一个 HTML 文件（伪扩展名）。

## 执行

```bash
python skills/prd-parse/scripts/prd_parse.py /tmp/prd-edge
python skills/prd-parse/scripts/prd_parse.py /tmp/prd-edge   # 第二次
python skills/prd-parse/scripts/prd_parse.py /tmp/prd-edge --force
```

## 期望

- 第一次：manifest warnings 含"扩展名 .docx 实际是 HTML，按 HTML 解析"，status=warning
- 第二次：status=skipped（mtime 未变，增量生效）
- 第三次：--force 重新解析，status 恢复 warning

# 场景 3：错误（无可解析文件 / 缺依赖指引）

## 输入与执行

```bash
python skills/prd-parse/scripts/prd_parse.py /tmp/empty-dir   # 空目录（无受支持扩展名）
python skills/prd-parse/scripts/prd_parse.py /tmp/no-such-path # 路径不存在
```

## 期望

- 空目录：exit 2，stderr 提示"未找到可解析文档"并列出受支持扩展名
- 路径不存在：exit 2，stderr 提示"目标不存在"
- （若本机未装 pymupdf）对 .pdf 文件：该文件 status=failed，error 含按当前解释器
  的 pip 安装指引，其余文件照常解析——单文件失败不拖垮整批
