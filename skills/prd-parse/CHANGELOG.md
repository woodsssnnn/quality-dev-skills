# prd-parse CHANGELOG

## 0.9.0.0（2026-10-19）

- 首个通用版本：pdf/doc/docx/xlsx/xls/html → 1:1 Markdown
- 输出契约：parsed/<stem>.md + images/ + manifest.json（warnings 绝不静默丢）
- docx/xlsx/html 纯 stdlib 零依赖；pdf/xls 可选依赖缺省时优雅降级并给安装指引
- 安全加固：文档包内 XML 拒绝 DOCTYPE/ENTITY 声明（实体扩展防护）；
  图片去重哈希使用 SHA-256
