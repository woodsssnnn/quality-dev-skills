# Changelog

All notable changes to this project are documented here.

> **权威版本历史（机器可读）在 [version.json](version.json)** —— 本文件仅做导航与摘要。
> The authoritative, machine-readable history lives in [version.json](version.json);
> this file is a navigation summary.

## Recent Releases

### 0.9.0.1 (2026-10-19)

- ZCode plugin mechanism adaptation: `platforms/zcode/` adapter +
  self-contained plugin builder (`scripts/build-zcode-plugin.py`)

### 0.9.0.0 (2026-10-19)

- **governance/**: code-level governance runtime — declarative PostToolUse rule
  gating (block via exit 2), verification machine receipts, SHA-256 hash-chained
  event stream, SessionStart integrity self-check, neutral built-in rules
- **Domain-pack open mechanism**: spec + template + scaffolding + validator,
  zero built-in domain content
- **prd-parse** skill: lossless 1:1 parsing of pdf/doc/docx/xlsx/xls/html
- Neutral `reviewer`/`verifier`/`db-migrator` agent templates; qgw-init gate wiring
- Repo-wide neutrality cleanup + banned-terms CI gate; version consistency at 0.9.0.0

For earlier releases (0.5 → 0.8.3), see the `changelog` array in
[version.json](version.json).
