# 场景 2：边界（扩展名与实际格式不符 + 增量跳过）

## 输入

/tmp/prd-edge/导出需求.docx —— 实际内容是一个 HTML 文件（伪扩展名）：

```html
<html><body><h1>导出功能</h1><p>支持按月导出报表。</p></body></html>
```

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
