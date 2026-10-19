---
name: prd-parse
category: document-processing
description: |-
  Use when parsing raw requirement documents (需求文档/PRD) in pdf/doc/docx/xlsx/xls/html
  format into lossless 1:1 Markdown before task extraction. Triggers on: 解析需求文档,
  解析PRD, PRD 解析, pdf 转任务, docx 需求, xlsx 需求, 需求文档解析, prd parse.
allowed-tools:
  - Read
  - Bash(python *)
metadata:
  version: 0.9.0.0
integration:
  extends: []
  extended_by: []
  shares_artifacts_with:
    - quality-gate-workflow
---

# PRD 原始文档解析

把客户/业务方发来的原始需求文档（**pdf / doc / docx / xlsx / xls / html**）机械解析成
1:1 Markdown——文字全量、表格保真、图片全部落盘。解析是纯机械步骤；功能点抽取、
任务拆分、横切关注点识别是上层任务流程（如 quality-gate-workflow 的 Gate 1）的活，
两层职责分离。

## 用法

```bash
# 目录模式：扫所有原始文档 → <目录>/parsed/
python skills/prd-parse/scripts/prd_parse.py <PRD目录> --json

# 单文件模式 / 强制重解析
python skills/prd-parse/scripts/prd_parse.py <某文件>.pdf
python skills/prd-parse/scripts/prd_parse.py <PRD目录> --force
```

**注意用 `python` 而不是 `python3`**——Windows 上两者可能指向不同解释器（包只装在其中之一）。

## 输出契约

```
<PRD目录>/parsed/
  <stem>.md              1:1 正文：标题层级/段落/列表/GFM 表格/图片引用
  images/<stem>/NN.ext   图片按文中出现顺序落盘（同内容自动去重）
  manifest.json          每源文件 {status, backend, pages/sheets, text_chars, tables, images, warnings[]}
```

- `parsed/<stem>.md` 已存在且源文件 mtime 未变 → 跳过（增量）；`--force` 强制重解析
- 同名不同扩展名（如 `报告.pdf` + `报告.docx`）→ 输出 `<stem>.<ext>.md` 避免冲突
- **agent 后续动作**：读 manifest 处理 warnings → 抽查 `parsed/*.md` 开头确认质量 →
  手写 `index.md`（概要 + 核心功能点 + 影响模块）供上层任务流程消费

## 1:1 验收口径

| 维度 | 承诺 |
|---|---|
| 文字 | 全段落全量，`text_chars` 报数；标题按字号阶梯/Heading 样式映射 `#` 层级 |
| 表格 | 无跨格 → GFM；有 rowspan/colspan/嵌套 → **原样内嵌 HTML** 保真（GFM 表达不了跨格） |
| 图片 | 全部落盘 + 正文位置引用；同内容去重；扫描页输出整页快照 |
| 不可保全项 | manifest `warnings[]` 明示，**绝不静默丢**（扫描页/远程图/emf 矢量图/xls 内嵌图…） |
| 安全 | 文档包内 XML 含 DOCTYPE/ENTITY 声明即拒绝解析（实体扩展防护，纯 stdlib） |

## 各格式后端与依赖

| 格式 | backend | 依赖 |
|---|---|---|
| pdf | pymupdf（字号阶梯判标题、find_tables 抽表、图片按内容去重、扫描页快照） | `pymupdf`（三方，可选） |
| docx | stdlib zip+XML（含文本框文字、vMerge/gridSpan 跨格表、页眉页脚文字） | 无 |
| xlsx | stdlib zip+XML（sheet/合并单元格/日期/公式缓存值/sheet 内嵌图，绕开 openpyxl） | 无 |
| xls | xlrd（sheet/合并/日期） | `xlrd`（三方，可选） |
| html | stdlib HTMLParser（编码嗅探 utf-8/gb18030、data-URI 图落盘、本地图复制、远程图记录） | 无 |
| doc | 转换链：soffice → WPS/Word COM → 都无则 status=failed 并指引用户另存 .docx | soffice 或 WPS |

可选依赖安装（缺依赖时对应文件 failed 并给指引，其余格式照常——docx/xlsx/html 零依赖开箱即用）：

```bash
python -m pip install pymupdf xlrd
```

扩展名与实际格式不符（`.doc` 实为 HTML/docx 等）按魔数嗅探纠正并给 warning。

## 已知边界（如实声明）

- **扫描版 PDF**：无文本层 → 整页 PNG 快照（≤10 页）+ warning，**不做 OCR**——LLM 可读图
- **复杂跨格表格**：原样内嵌 HTML，grep 仍可命中文字，渲染需支持 HTML 的查看器
- **HTML 远程图片**：只记录 URL 不联网下载（离线解析原则）
- **emf/wmf 矢量图**：落盘但多数读图工具打不开，warning 提示人工转 png
- **PDF 矢量流程图**：文字会保留，图形结构不重建——需看图时对照整页快照
- **.doc**：依赖本机 soffice/WPS/Word，三者皆无时需用户手动另存 .docx

## 排障

| 症状 | 修复 |
|---|---|
| `缺少依赖 fitz/pymupdf` | 按报错里的当前解释器装：`"<sys.executable>" -m pip install pymupdf` |
| .doc 转 failed | 装 WPS 或 LibreOffice，或手动另存 .docx 后重跑 |
| xlsx 报 zip 损坏 | 文件可能是 .xls 伪名或加密导出，看 manifest 的嗅探 warning |
| 解析结果可疑 | 先看 `manifest.json` 的 warnings 与 text_chars，再抽查对应页原文 |
| XML 拒绝解析（DOCTYPE/ENTITY） | 文档包内 XML 含实体声明，疑似恶意构造或损坏；人工检查源文件 |

## 验证

```bash
python -m py_compile skills/prd-parse/scripts/prd_parse.py
printf '<h1>标题</h1><table><tr><td>a</td><td>b</td></tr></table>' > /tmp/t.html
python skills/prd-parse/scripts/prd_parse.py /tmp/t.html
```

评测场景见 [evaluations/](evaluations/)（正常/边界/错误各一）。
