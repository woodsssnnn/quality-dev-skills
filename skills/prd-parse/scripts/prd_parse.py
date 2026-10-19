#!/usr/bin/env python3
"""prd-parse — 需求文档 1:1 解析

把 PRD 原始文档（pdf/doc/docx/xlsx/xls/html）机械解析为 Markdown，信息 1:1 不丢失：
文字全量、表格保真（GFM 或原样 HTML）、图片全部落盘。摘要与功能点抽取不在此脚本——
那是上层任务流程里 agent 读产物后的活。

Usage:
    python prd_parse.py <PRD目录或单文件> [--out DIR] [--force] [--json] [-v]

Output（默认 <源目录>/parsed/）:
    <stem>.md            1:1 正文（标题层级/段落/列表/表格/图片引用）
    images/<stem>/NN.ext 抽取的图片，按文中出现顺序命名
    manifest.json        每源文件 {status, backend, pages/sheets, text_chars, tables, images, warnings[]}

依赖：pdf 需要 pymupdf；xls 需要 xlrd；docx/xlsx/html 纯 stdlib；.doc 需 soffice 或 WPS。
缺依赖时对应文件 status=failed 并在 manifest 给出安装指引，其余文件照常。

Exit codes: 0=全部成功(含跳过)  1=有文件失败  2=用法/环境错误
"""

import argparse
import base64
import collections
import contextlib
import datetime as _dt
import hashlib
import html as _html
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

SUPPORTED_EXTS = {".pdf", ".doc", ".docx", ".xlsx", ".xls", ".html", ".htm"}
SKIP_PREFIXES = ("~$", ".~")  # Office 锁文件等临时文件
KNOWN_IMAGE_EXTS = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "tiff", "emf", "wmf", "svg"}

log = logging.getLogger("prd_parse")


def configure_stdio() -> None:
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")


def safe_xml(data: bytes):
    """实体扩展防护：文档包内的 XML 是不可信输入，含 DOCTYPE/ENTITY 声明即拒绝
    （合法的 docx/xlsx 包不含这些声明），避免实体扩展造成的资源耗尽。
    纯 stdlib 实现，防护目标与 defusedxml 相同。"""
    head = data[:4096].lstrip()
    if b"<!DOCTYPE" in head or b"<!ENTITY" in head.upper():
        raise ValueError("XML 含 DOCTYPE/ENTITY 声明，已拒绝解析（疑似实体扩展攻击）")
    return ET.fromstring(data)


# ─── 通用工具 ───────────────────────────────────────────────────────────

def sanitize_stem(name: str) -> str:
    stem = re.sub(r'[\\/:*?"<>|]+', "_", name).strip().strip(".")
    return stem[:80] or "unnamed"


def md_escape_cell(text: str) -> str:
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")


class ImageStore:
    """图片落盘 + 按内容去重，返回文件名。"""

    def __init__(self, img_dir: Path):
        self.img_dir = img_dir
        self.img_dir.mkdir(parents=True, exist_ok=True)
        self.by_hash = {}
        self.count = 0

    def save(self, data: bytes, ext: str) -> str:
        digest = hashlib.sha256(data).hexdigest()
        if digest in self.by_hash:
            return self.by_hash[digest]
        ext = ext.lower().lstrip(".")
        if ext not in KNOWN_IMAGE_EXTS:
            ext = "png"
        self.count += 1
        fname = f"{self.count:02d}.{ext}"
        (self.img_dir / fname).write_bytes(data)
        self.by_hash[digest] = fname
        return fname

    def copy_file(self, src: Path) -> str:
        return self.save(src.read_bytes(), src.suffix)


class Cell:
    __slots__ = ("text", "rowspan", "colspan", "is_header")

    def __init__(self, text="", rowspan=1, colspan=1, is_header=False):
        self.text, self.rowspan, self.colspan, self.is_header = text, rowspan, colspan, is_header


class TableModel:
    """跨格感知的表格模型：无跨格 → GFM；有跨格/嵌套 → 原样 HTML（GFM 表达不了 rowspan/colspan）。

    vMerge/rowspan 续行不放占位 cell——HTML 语义由起始格的 rowspan 覆盖；
    因此 to_gfm 仅在无跨格时调用（此时每行 cell 齐全）。
    """

    def __init__(self):
        self.rows = []

    def start_row(self) -> None:
        self.rows.append([])

    def add_cell(self, cell: Cell) -> None:
        if not self.rows:
            self.start_row()
        self.rows[-1].append(cell)

    @property
    def has_span(self) -> bool:
        return any(c.rowspan > 1 or c.colspan > 1 for row in self.rows for c in row)

    def to_gfm(self) -> str:
        if not self.rows:
            return ""
        width = max(len(r) for r in self.rows)
        norm = [[md_escape_cell(c.text) for c in r] + [""] * (width - len(r)) for r in self.rows]
        lines = ["| " + " | ".join(norm[0]) + " |",
                 "| " + " | ".join(["---"] * width) + " |"]
        lines += ["| " + " | ".join(r) + " |" for r in norm[1:]]
        return "\n".join(lines)

    def to_html(self) -> str:
        out = ["<table>"]
        for row in self.rows:
            out.append("<tr>")
            for c in row:
                tag = "th" if c.is_header else "td"
                attrs = (f' rowspan="{c.rowspan}"' if c.rowspan > 1 else "") + \
                        (f' colspan="{c.colspan}"' if c.colspan > 1 else "")
                text = _html.escape(c.text).replace("\n", "<br>")
                out.append(f"<{tag}{attrs}>{text}</{tag}>")
            out.append("</tr>")
        out.append("</table>")
        return "".join(out)


def sniff_format(path: Path) -> str:
    try:
        with path.open("rb") as fh:
            head = fh.read(512)
    except OSError:
        return "unknown"
    if head.startswith(b"%PDF"):
        return "pdf"
    if head.startswith(b"PK\x03\x04"):
        return "zip"
    if head.startswith(b"\xd0\xcf\x11\xe0"):
        return "ole"
    low = head.lower()
    if low.lstrip()[:1] == b"<" or b"<html" in low or b"<!doctype html" in low:
        return "html"
    return "unknown"


# ─── PDF（pymupdf）─────────────────────────────────────────────────────

def parse_pdf(src: Path, md_path: Path, store: ImageStore, stats: dict) -> None:
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf  # 兼容旧包名
    Rect = pymupdf.Rect

    doc = pymupdf.open(src)
    stats["pages"] = doc.page_count
    if doc.metadata and doc.metadata.get("title"):
        stats["doc_title"] = doc.metadata["title"]

    def overlap_ratio(block_rect, table_rect) -> float:
        inter = block_rect & table_rect
        if inter.is_empty or block_rect.get_area() <= 0:
            return 0.0
        return inter.get_area() / block_rect.get_area()

    # pass 1：缓存每页 dict+表格；字号直方图排除表格内文字（表格字号常小于正文，会拉低基准）
    page_cache = []
    size_weight = collections.Counter()
    for page in doc:
        try:
            tables = page.find_tables().tables
        except Exception as e:
            tables = []
            log.debug("find_tables 失败: %s", e)
        table_rects = [Rect(t.bbox) for t in tables]
        d = page.get_text("dict")
        page_cache.append((d, tables, table_rects))
        for block in d["blocks"]:
            if block["type"] != 0:
                continue
            r = Rect(block["bbox"])
            if any(overlap_ratio(r, tr) > 0.5 for tr in table_rects):
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    stripped = span["text"].strip()
                    if stripped:
                        size_weight[round(span["size"] * 2) / 2] += len(stripped)
    body_size = size_weight.most_common(1)[0][0] if size_weight else 10.0
    heading_sizes = sorted({s for s in size_weight if s > body_size * 1.13}, reverse=True)

    def level_for_size(size: float) -> int:
        if not heading_sizes or size < heading_sizes[-1] - 0.3:
            return 0
        for i, s in enumerate(heading_sizes):
            if size >= s - 0.3:
                return min(i + 1, 4)
        return 0

    parts, snapshot_count = [], 0
    for pno, (d, tables, table_rects) in enumerate(page_cache, 1):
        page = doc[pno - 1]
        parts.append(f"\n<!-- page {pno} -->\n")

        items = []
        for block in d["blocks"]:
            r = Rect(block["bbox"])
            if block["type"] == 0:
                if any(overlap_ratio(r, tr) > 0.5 for tr in table_rects):
                    continue  # 表内文字由表格输出，避免重复
                items.append((r.y0, r.x0, "text", block))
            else:
                items.append((r.y0, r.x0, "image", block))
        for t in tables:
            items.append((t.bbox[1], t.bbox[0], "table", t))
        items.sort(key=lambda it: (round(it[0]), it[1]))

        page_text_len = 0
        page_parts = []

        def emit_text_block(block) -> None:
            # 行级标题判定：相邻块可能把正文行和标题行合并（PyMuPDF 按版面邻近分块）
            nonlocal page_text_len
            para_buf, head_buf, head_lvl = [], [], 0

            def flush_para():
                nonlocal page_text_len
                if para_buf:
                    text = "\n".join(para_buf)
                    page_parts.append("\n\n" + text + "\n")
                    page_text_len += len(text)
                    stats["text_chars"] += len(text)
                    para_buf.clear()

            def flush_head():
                nonlocal page_text_len
                if head_buf:
                    text = " ".join(head_buf)
                    page_parts.append("\n\n" + "#" * head_lvl + " " + text + "\n")
                    page_text_len += len(text)
                    stats["text_chars"] += len(text)
                    head_buf.clear()

            for line in block["lines"]:
                text = "".join(span["text"] for span in line["spans"]).strip()
                if not text:
                    continue
                size = max((span["size"] for span in line["spans"]
                            if span["text"].strip()), default=0.0)
                lvl = level_for_size(size)
                if lvl:
                    flush_para()
                    if head_lvl != lvl:
                        flush_head()
                        head_lvl = lvl
                    head_buf.append(text)
                else:
                    flush_head()
                    head_lvl = 0
                    para_buf.append(text)
            flush_para()
            flush_head()

        for _y, _x, kind, payload in items:
            if kind == "table":
                model = TableModel()
                for row in payload.extract():
                    model.start_row()
                    for cell in row:
                        model.add_cell(Cell("" if cell is None else str(cell).strip()))
                stats["tables"] += 1
                page_parts.append("\n\n" + (model.to_gfm() if not model.has_span else model.to_html()) + "\n")
            elif kind == "image":
                data = payload.get("image")
                if not data:
                    stats["warnings"].append(f"第 {pno} 页有图片块但无法提取字节（超大内嵌图?），已跳过")
                    continue
                fname = store.save(data, payload.get("ext", "png"))
                stats["images"] += 1
                page_parts.append(f"\n\n![image-p{pno}](images/{md_path.stem}/{fname})\n")
            else:
                emit_text_block(payload)

        if page_text_len == 0:
            if snapshot_count < 10:
                pix = page.get_pixmap(dpi=150)
                fname = store.save(pix.tobytes("png"), "png")
                stats["images"] += 1
                page_parts.append(f"\n![page-snapshot-p{pno}](images/{md_path.stem}/{fname})\n")
                snapshot_count += 1
            stats["warnings"].append(f"第 {pno} 页无文本层（扫描页/图片页），已输出整页快照供读图")

        parts.extend(page_parts)

    md_path.write_text("".join(parts), encoding="utf-8")
    doc.close()
    stats["backend"] = "pymupdf"


# ─── DOCX（stdlib zipfile + ElementTree）───────────────────────────────

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
V_NS = "{urn:schemas-microsoft-com:vml}"


def parse_docx(src: Path, md_path: Path, store: ImageStore, stats: dict) -> None:
    zf = zipfile.ZipFile(src)
    doc_xml = safe_xml(zf.read("word/document.xml"))

    # styles：styleId → 标题级别 / 是否列表样式
    style_heading, style_list = {}, set()
    try:
        styles = safe_xml(zf.read("word/styles.xml"))
        for style in styles.findall(f"{W_NS}style"):
            style_id = style.get(f"{W_NS}styleId", "")
            name_el = style.find(f"{W_NS}name")
            name = (name_el.get(f"{W_NS}val", "") if name_el is not None else "").lower()
            m = re.search(r"(?:heading|标题)\s*(\d)", name)
            if m:
                style_heading[style_id] = min(int(m.group(1)), 6)
            elif name in ("title", "标题"):
                style_heading[style_id] = 1
            if re.search(r"list|列表", f"{name} {style_id.lower()}"):
                style_list.add(style_id)  # List Bullet/ListParagraph 等的编号挂在样式上
    except (KeyError, ValueError):
        pass

    # rels：rId → target（图片/超链接）
    rel_targets = {}
    if "word/_rels/document.xml.rels" in zf.namelist():
        for rel in safe_xml(zf.read("word/_rels/document.xml.rels")):
            rel_targets[rel.get("Id")] = rel.get("Target", "")

    def image_ref(rid: str) -> str:
        target = rel_targets.get(rid, "")
        if not target:
            stats["warnings"].append(f"图片引用 {rid} 无对应关系条目，已跳过")
            return ""
        if re.match(r"^(https?|ftp)://", target, re.I):
            stats["warnings"].append(f"外链图片未下载: {target[:120]}")
            return f"![external-image]({target})"
        zip_path = "word/" + target.lstrip("/")
        try:
            data = zf.read(zip_path)
        except KeyError:
            stats["warnings"].append(f"图片 {target} 不在包内，已跳过")
            return ""
        ext = Path(target).suffix or "png"
        if ext.lower().lstrip(".") in {"emf", "wmf"}:
            stats["warnings"].append(f"{target} 是 emf/wmf 矢量图，读图工具可能打不开，建议人工转 png")
        fname = store.save(data, ext)
        stats["images"] += 1
        return f"\n![image](images/{md_path.stem}/{fname})\n"

    def collect_inline(elem) -> str:
        out = []
        for node in elem:
            tag = node.tag if isinstance(node.tag, str) else ""
            if tag == f"{W_NS}t":
                out.append(node.text or "")
            elif tag == f"{W_NS}tab":
                out.append("\t")
            elif tag in (f"{W_NS}br", f"{W_NS}cr"):
                out.append("\n")
            elif tag == f"{W_NS}hyperlink":
                text = collect_inline(node)
                url = rel_targets.get(node.get(f"{R_NS}id", ""))
                out.append(f"[{text}]({url})" if url and text else text)
            elif tag in (f"{W_NS}drawing", f"{W_NS}pict", f"{W_NS}object"):
                for blip in node.iter(f"{A_NS}blip"):
                    ref = image_ref(blip.get(f"{R_NS}embed", ""))
                    if ref:
                        out.append(ref)
                for imgdata in node.iter(f"{V_NS}imagedata"):
                    ref = image_ref(imgdata.get(f"{R_NS}id", ""))
                    if ref:
                        out.append(ref)
                for t in node.iter(f"{W_NS}t"):  # 图形/文本框里的字也是信息
                    out.append(t.text or "")
            elif tag == f"{W_NS}pPr":
                continue
            else:
                out.append(collect_inline(node))
        return "".join(out)

    def para_md(p_elem) -> str:
        style_el = p_elem.find(f"{W_NS}pPr/{W_NS}pStyle")
        style_id = style_el.get(f"{W_NS}val", "") if style_el is not None else ""
        level = style_heading.get(style_id, 0)
        text = collect_inline(p_elem).strip("\n").strip()
        if not text:
            return ""
        stats["text_chars"] += len(text)
        is_list = (p_elem.find(f"{W_NS}pPr/{W_NS}numPr") is not None
                   or style_id in style_list)
        if is_list:
            return "\n\n- " + text.replace("\n", "\n  ") + "\n"
        if level:
            return "\n\n" + "#" * level + " " + text + "\n"
        return "\n\n" + text + "\n"

    def table_md(tbl_elem) -> str:
        model = TableModel()
        restart_by_col = {}  # 列号 → 该列当前 vMerge 起始 Cell（跨行聚合）
        nested = [False]

        def cell_text(tc) -> str:
            chunks = []
            for child in tc:
                if child.tag == f"{W_NS}p":
                    chunks.append(collect_inline(child).strip())
                elif child.tag == f"{W_NS}tbl":
                    nested[0] = True
                    chunks.append(table_md(child))
            return "\n".join(c for c in chunks if c)

        for tr in tbl_elem.findall(f"{W_NS}tr"):
            model.start_row()
            col = 0
            for tc in tr.findall(f"{W_NS}tc"):
                tc_pr = tc.find(f"{W_NS}tcPr")
                colspan, vmerge = 1, None
                if tc_pr is not None:
                    gs = tc_pr.find(f"{W_NS}gridSpan")
                    if gs is not None:
                        try:
                            colspan = max(1, int(gs.get(f"{W_NS}val", "1")))
                        except ValueError:
                            colspan = 1
                    vm = tc_pr.find(f"{W_NS}vMerge")
                    if vm is not None:
                        vmerge = vm.get(f"{W_NS}val", "continue")  # 无 val 即 continue
                text = cell_text(tc)
                if vmerge == "continue":
                    restart = restart_by_col.get(col)
                    if restart is not None:
                        restart.rowspan += 1
                        if text.strip():
                            restart.text += "\n" + text  # 续格偶尔带字 → 归并到起始格
                else:
                    cell = Cell(text, rowspan=1, colspan=colspan)
                    model.add_cell(cell)
                    if vmerge == "restart":
                        restart_by_col[col] = cell
                    else:
                        restart_by_col.pop(col, None)
                col += colspan
        stats["tables"] += 1
        if nested[0] or model.has_span:
            stats["warnings"].append("表格含合并单元格/嵌套表格，已按原样内嵌 HTML 保真")
            return "\n" + model.to_html() + "\n"
        return "\n" + model.to_gfm() + "\n"

    parts = []
    for child in doc_xml.find(f"{W_NS}body"):
        if child.tag == f"{W_NS}p":
            md = para_md(child)
            if md:
                parts.append(md)
        elif child.tag == f"{W_NS}tbl":
            parts.append(table_md(child))

    # 页眉/页脚文字（常有版本号/密级等信息）
    for name in zf.namelist():
        if re.match(r"word/(header|footer)\d*\.xml$", name):
            try:
                texts = [t.text or "" for t in safe_xml(zf.read(name)).iter(f"{W_NS}t")]
            except ET.ParseError:
                continue
            joined = "".join(texts).strip()
            if joined and not re.fullmatch(r"[\s\d]*", joined):
                parts.append(f"\n> 页眉页脚补充（{Path(name).stem}）：{joined}\n")

    md_path.write_text("".join(parts), encoding="utf-8")
    stats["backend"] = "docx-stdlib"


# ─── XLSX（stdlib zipfile + ElementTree，绕开 openpyxl）────────────────

SS_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
SS_R_ATTR = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
DATE_BUILTIN_IDS = set(range(14, 23)) | {45, 46, 47}
EXCEL_EPOCH = _dt.datetime(1899, 12, 30)


def parse_xlsx(src: Path, md_path: Path, store: ImageStore, stats: dict) -> None:
    zf = zipfile.ZipFile(src)
    shared = []
    if "xl/sharedStrings.xml" in zf.namelist():
        for si in safe_xml(zf.read("xl/sharedStrings.xml")).findall(f"{SS_NS}si"):
            shared.append("".join(t.text or "" for t in si.iter(f"{SS_NS}t")))

    # 样式 → 日期格式判定
    custom_date_fmts, date_styles = {}, set()
    if "xl/styles.xml" in zf.namelist():
        styles = safe_xml(zf.read("xl/styles.xml"))
        for fmt in styles.iter(f"{SS_NS}numFmt"):
            code = fmt.get("formatCode", "")
            if re.search(r"[yYmMdDhHsS]", code) and "#" not in code:
                custom_date_fmts[fmt.get("numFmtId", "")] = True
        xfs = styles.find(f"{SS_NS}cellXfs")
        if xfs is not None:
            for idx, xf in enumerate(xfs.findall(f"{SS_NS}xf")):
                fid = xf.get("numFmtId", "")
                if fid in DATE_BUILTIN_IDS or custom_date_fmts.get(fid):
                    date_styles.add(idx)

    wb = safe_xml(zf.read("xl/workbook.xml"))
    wb_rels = {}
    if "xl/_rels/workbook.xml.rels" in zf.namelist():
        for rel in safe_xml(zf.read("xl/_rels/workbook.xml.rels")):
            wb_rels[rel.get("Id")] = rel.get("Target", "")

    def col_to_idx(letters: str) -> int:
        n = 0
        for ch in letters:
            n = n * 26 + (ord(ch) - 64)
        return n - 1

    def cell_ref_pos(ref: str):
        m = re.match(r"([A-Z]+)(\d+)", ref or "")
        return (int(m.group(2)) - 1, col_to_idx(m.group(1))) if m else (None, None)

    def fmt_value(c_el, style_idx) -> str:
        t = c_el.get("t", "")
        v_el = c_el.find(f"{SS_NS}v")
        f_el = c_el.find(f"{SS_NS}f")
        v = v_el.text if v_el is not None else ""
        if t == "s":
            try:
                return shared[int(v)]
            except (ValueError, IndexError):
                return v
        if t == "inlineStr":
            is_el = c_el.find(f"{SS_NS}is")
            return "".join(x.text or "" for x in is_el.iter(f"{SS_NS}t")) if is_el is not None else ""
        if t == "b":
            return "TRUE" if v == "1" else "FALSE"
        if t == "e":
            return f"#错误:{v}"
        if style_idx in date_styles and v:
            try:
                num = float(v)
                base = EXCEL_EPOCH + _dt.timedelta(days=num)
                return base.strftime("%Y-%m-%d %H:%M") if num % 1 else base.strftime("%Y-%m-%d")
            except ValueError:
                pass
        if f_el is not None and f_el.text:
            formula = "=" + f_el.text.strip()
            return f"{formula}（计算值: {v}）" if v else formula
        return v

    parts = []
    sheets_el = wb.find(f"{SS_NS}sheets")
    for sheet in (sheets_el if sheets_el is not None else []):
        name = sheet.get("name", "sheet")
        target = wb_rels.get(sheet.get(SS_R_ATTR, ""), "")
        if not target:
            continue
        zip_path = target if target.startswith("xl/") else "xl/" + target.lstrip("/")
        if zip_path not in zf.namelist():
            stats["warnings"].append(f"sheet 「{name}」的 xml（{target}）不在包内，跳过")
            continue
        el = safe_xml(zf.read(zip_path))
        sheet_data = el.find(f"{SS_NS}sheetData")
        cells = {}
        for row in (sheet_data if sheet_data is not None else []):
            r_attr = row.get("r")
            row_num = int(r_attr) - 1 if r_attr and r_attr.isdigit() else None
            if row_num is None:
                row_num = (max(r for r, _ in cells) + 1) if cells else 0
            seq = 0
            for c in row.findall(f"{SS_NS}c"):
                c_row, c_col = cell_ref_pos(c.get("r", ""))
                if c_row is None:
                    c_row, c_col = row_num, seq
                seq += 1
                s_attr = c.get("s")
                try:
                    s_idx = int(s_attr) if s_attr is not None else -1
                except ValueError:
                    s_idx = -1
                text = fmt_value(c, s_idx).strip()
                if text:
                    cells[(c_row, c_col)] = text

        merged = []
        mc = el.find(f"{SS_NS}mergeCells")
        if mc is not None:
            for m_el in mc.findall(f"{SS_NS}mergeCell"):
                rng = re.match(r"([A-Z]+\d+):([A-Z]+\d+)", m_el.get("ref", ""))
                if rng:
                    (r1, c1), (r2, c2) = cell_ref_pos(rng.group(1)), cell_ref_pos(rng.group(2))
                    top = cells.get((r1, c1), "")
                    for rr in range(r1, r2 + 1):
                        for cc in range(c1, c2 + 1):
                            cells.setdefault((rr, cc), top)
                    merged.append(m_el.get("ref"))

        hidden = "（隐藏 sheet）" if sheet.get("state") == "hidden" else ""
        parts.append(f"\n## Sheet: {name}{hidden}\n")
        stats["sheets"] = stats.get("sheets", 0) + 1
        if not cells:
            parts.append("（空 sheet）\n")
            continue
        col_min = min(c for _, c in cells)
        col_max = max(c for _, c in cells)
        rows_present = sorted({r for r, _ in cells
                               if any(cells.get((r, c), "").strip() for c in range(col_min, col_max + 1))})
        if not rows_present:
            parts.append("（空 sheet）\n")
            continue
        width = col_max - col_min + 1
        lines = []
        for r in rows_present:
            vals = [md_escape_cell(cells.get((r, c), "")) for c in range(col_min, col_max + 1)]
            lines.append("| " + " | ".join(vals) + " |")
        parts.append("\n".join([lines[0], "| " + " | ".join(["---"] * width) + " |"] + lines[1:]) + "\n")
        stats["tables"] += 1
        stats["text_chars"] += sum(len(v) for v in cells.values())
        if merged:
            stats["warnings"].append(f"sheet 「{name}」含 {len(merged)} 处合并单元格，值已填充到整个合并区域")

        # sheet 内嵌图片：sheetN.xml.rels → drawing → drawing rels → media
        sheet_rels_name = zip_path.replace("worksheets/", "worksheets/_rels/") + ".rels"
        if sheet_rels_name in zf.namelist():
            for rel in safe_xml(zf.read(sheet_rels_name)):
                if "drawing" not in (rel.get("Type") or ""):
                    continue
                dtarget = rel.get("Target", "").replace("../", "xl/")
                drels = dtarget.replace("drawings/", "drawings/_rels/") + ".rels"
                drel_map = {}
                if drels in zf.namelist():
                    for dr in safe_xml(zf.read(drels)):
                        drel_map[dr.get("Id")] = dr.get("Target", "").replace("../", "xl/")
                if dtarget in zf.namelist():
                    for blip in safe_xml(zf.read(dtarget)).iter(f"{A_NS}blip"):
                        media = drel_map.get(blip.get(f"{R_NS}embed", ""))
                        if media and media in zf.namelist():
                            fname = store.save(zf.read(media), Path(media).suffix)
                            stats["images"] += 1
                            parts.append(f"\n![{name}-image](images/{md_path.stem}/{fname})\n")

    md_path.write_text("".join(parts), encoding="utf-8")
    stats["backend"] = "xlsx-stdlib"


# ─── XLS（xlrd）────────────────────────────────────────────────────────

def parse_xls(src: Path, md_path: Path, store: ImageStore, stats: dict) -> None:
    import xlrd
    try:
        book = xlrd.open_workbook(str(src), formatting_info=True)
    except Exception:
        book = xlrd.open_workbook(str(src))
        stats["warnings"].append("无法读取合并单元格信息（formatting_info 不支持）")

    parts = []
    for sheet in book.sheets():
        merged = [tuple(m) for m in getattr(sheet, "merged_cells", [])]
        cells = {}
        for r in range(sheet.nrows):
            for c in range(sheet.ncols):
                cell = sheet.cell(r, c)
                if cell.ctype == xlrd.XL_CELL_DATE:
                    text = xlrd.xldate_as_datetime(cell.value, book.datemode).strftime("%Y-%m-%d %H:%M")
                elif cell.ctype == xlrd.XL_CELL_BOOLEAN:
                    text = "TRUE" if cell.value else "FALSE"
                elif cell.ctype == xlrd.XL_CELL_ERROR:
                    text = f"#错误:{cell.value}"
                elif cell.ctype == xlrd.XL_CELL_NUMBER:
                    text = f"{cell.value:g}"
                else:
                    text = str(cell.value or "")
                if text.strip():
                    cells[(r, c)] = text
        for r1, r2, c1, c2 in merged:
            top = cells.get((r1, c1), "")
            for rr in range(r1, r2):
                for cc in range(c1, c2):
                    cells.setdefault((rr, cc), top)

        parts.append(f"\n## Sheet: {sheet.name}\n")
        if not cells:
            parts.append("（空 sheet）\n")
            continue
        rows_present = sorted({r for r, _ in cells})
        col_min = min(c for _, c in cells)
        col_max = max(c for _, c in cells)
        width = col_max - col_min + 1
        lines = []
        for r in rows_present:
            vals = [md_escape_cell(cells.get((r, c), "")) for c in range(col_min, col_max + 1)]
            lines.append("| " + " | ".join(vals) + " |")
        parts.append("\n".join([lines[0], "| " + " | ".join(["---"] * width) + " |"] + lines[1:]) + "\n")
        stats["tables"] += 1
        stats["text_chars"] += sum(len(v) for v in cells.values())
        if merged:
            stats["warnings"].append(f"sheet 「{sheet.name}」含 {len(merged)} 处合并单元格，值已填充到整个合并区域")

    md_path.write_text("".join(parts), encoding="utf-8")
    stats["backend"] = "xlrd"
    stats["sheets"] = book.nsheets


# ─── HTML（stdlib HTMLParser）──────────────────────────────────────────

SKIP_SUBTREE = {"script", "style", "svg", "iframe", "canvas", "audio", "video", "noscript", "template", "head"}
BLOCK_TAGS = {"p", "div", "section", "article", "main", "header", "footer", "nav", "aside",
              "blockquote", "ul", "ol", "li", "table", "tr", "td", "th", "thead", "tbody", "tfoot",
              "h1", "h2", "h3", "h4", "h5", "h6", "pre", "hr", "br", "figure", "figcaption",
              "dl", "dt", "dd", "form", "fieldset", "details", "summary", "address", "title"}


class HtmlToMd(HTMLParser):
    """事件流 → Markdown。表格走 span 感知模型：无跨格 GFM，有跨格原样回显 HTML。"""

    def __init__(self, store: ImageStore, img_prefix: str, base_dir: Path, stats: dict):
        super().__init__(convert_charrefs=True)
        self.store, self.img_prefix, self.base_dir, self.stats = store, img_prefix, base_dir, stats
        self.out = []
        self.para = []           # 行内缓冲
        self.heading = None      # (level, buffer)
        self.list_stack = []     # [[tag, counter], ...]
        self.li_buf = None
        self.link_stack = []     # [(buffer, mark)]  </a> 时回包 [text](href)
        self.quote_depth = 0
        self.pre_depth = 0
        self.pre_buf = []
        self.skip_depth = 0
        self.skip_capture_title = False
        self.in_title = False
        self.title = None
        self.first_h1 = None
        self.table_depth = 0
        self.tbl_model = None
        self.cell_buf = None
        self.cell_meta = None
        self.table_raw = []      # 表内事件回显（有跨格时原样内嵌）
        self.table_span = False
        self.table_nested = False
        self.pending_title = ""

    # ---- 当前接收文本的缓冲 ----
    def _buf(self):
        if self.in_title:
            return None  # 走 pending_title
        if self.cell_buf is not None:
            return self.cell_buf
        if self.heading is not None:
            return self.heading[1]
        if self.li_buf is not None:
            return self.li_buf
        return self.para

    def _prefix(self) -> str:
        return "> " * self.quote_depth if self.quote_depth else ""

    def _emit(self, text: str) -> None:
        if text:
            self.out.append(("\n" if self.out else "") + text + "\n")

    def flush_para(self) -> None:
        text = "".join(self.para).strip()
        if text:
            self._emit(self._prefix() + text)
            self.stats["text_chars"] += len(text)
        self.para = []

    # ---- 图片 ----
    def _img(self, attrs: dict) -> None:
        src_url = (attrs.get("src") or attrs.get("data-src") or "").strip()
        alt = attrs.get("alt") or "image"
        if not src_url:
            return
        if src_url.startswith("data:image"):
            m = re.match(r"data:image/([\w.+-]+);base64,(.*)", src_url, re.S)
            if m:
                try:
                    fname = self.store.save(base64.b64decode(m.group(2)), m.group(1).split("+")[0])
                    ref = f"![{alt}]({self.img_prefix}{fname})"
                    self.stats["images"] += 1
                except Exception:
                    ref = None
                    self.stats["warnings"].append(f"data URI 图片解码失败: {alt}")
            else:
                ref = None
                self.stats["warnings"].append(f"data URI 图片格式无法解析: {src_url[:60]}")
        elif re.match(r"^(https?|ftp)://", src_url, re.I):
            ref = f"![{alt}]({src_url})"
            self.stats["warnings"].append(f"远程图片未下载（离线解析）: {src_url[:120]}")
        else:
            local = (self.base_dir / src_url.split("?")[0]).resolve()
            if local.is_file():
                fname = self.store.copy_file(local)
                ref = f"![{alt}]({self.img_prefix}{fname})"
                self.stats["images"] += 1
            else:
                ref = None
                self.stats["warnings"].append(f"本地图片缺失: {src_url}")
        if ref:
            buf = self._buf()
            if buf is self.cell_buf or (self.cell_buf is not None and buf is None):
                self.cell_buf.append(f" {ref} ")
            elif buf is not None:
                buf.append(f"\n{ref}\n")

    # ---- 表内原始回显 ----
    def _echo(self, token: str) -> None:
        self.table_raw.append(token)

    def _rebuild_tag(self, tag, attrs: dict) -> str:
        attr_str = "".join(f' {k}="{_html.escape(str(v), quote=True)}"' for k, v in attrs.items() if v is not None)
        return f"<{tag}{attr_str}>"

    # ---- 事件 ----
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.skip_depth:  # 忽略子树，但 head 里抓 title
            if tag == "title" and self.skip_capture_title:
                self.in_title = True
            elif tag in SKIP_SUBTREE:
                self.skip_depth += 1
            return
        if tag in SKIP_SUBTREE:
            self.flush_para()
            if tag == "head":
                self.skip_capture_title = True
            self.skip_depth = 1
            return
        if self.pre_depth:
            if tag == "pre":
                self.pre_depth += 1
            self.pre_buf.append(self._rebuild_tag(tag, attrs))
            return
        if self.table_depth:
            self._echo(self._rebuild_tag(tag, attrs))
            if tag == "table":
                self.table_depth += 1
                if self.table_depth > 1:
                    self.table_nested = True
            elif tag == "tr":
                self.tbl_model.start_row()
            elif tag in ("td", "th"):
                try:
                    rs = max(1, int(attrs.get("rowspan", "1")))
                    cs = max(1, int(attrs.get("colspan", "1")))
                except ValueError:
                    rs = cs = 1
                if rs > 1 or cs > 1:
                    self.table_span = True
                self.cell_buf = []
                self.cell_meta = (rs, cs, tag == "th")
            elif tag == "br" and self.cell_buf is not None:
                self.cell_buf.append("\n")
            elif tag == "img":
                self._img(attrs)
            return

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.flush_para()
            self.heading = (int(tag[1]), [])
        elif tag in ("ul", "ol"):
            self.flush_para()
            self.list_stack.append([tag, 0])
        elif tag == "li":
            self.flush_para()
            self.li_buf = []
        elif tag == "table":
            self.flush_para()
            self.table_depth = 1
            self.tbl_model = TableModel()
            self.table_raw = [self._rebuild_tag(tag, attrs)]
            self.table_span = False
            self.table_nested = False
        elif tag == "img":
            self._img(attrs)
        elif tag == "br":
            buf = self._buf()
            if buf is not None:
                buf.append("\n")
        elif tag == "hr":
            self.flush_para()
            self.out.append("\n---\n")
        elif tag == "pre":
            self.flush_para()
            self.pre_depth = 1
            self.pre_buf = []
        elif tag == "blockquote":
            self.flush_para()
            self.quote_depth += 1
        elif tag == "a":
            buf = self._buf()
            self.link_stack.append((attrs.get("href"), buf, len(buf) if buf is not None else 0))
        elif tag in BLOCK_TAGS:
            self.flush_para()
        # 行内标签（span/b/em/code...）不动作，文本自然流入当前缓冲

    def handle_startendtag(self, tag, attrs):
        if tag in ("img", "br"):
            self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if self.in_title and tag == "title":
            self.in_title = False
            self.title = self.pending_title.strip() or None
            self.pending_title = ""
            return
        if self.skip_depth:
            if tag in SKIP_SUBTREE:
                self.skip_depth -= 1
                if self.skip_depth == 0:
                    self.skip_capture_title = False
            return
        if self.pre_depth:
            if tag == "pre":
                self.pre_depth -= 1
                if self.pre_depth == 0:
                    self.out.append("\n```\n" + "".join(self.pre_buf).strip("\n") + "\n```\n")
                    self.pre_buf = []
                return
            self.pre_buf.append(f"</{tag}>")
            return
        if self.table_depth:
            self._echo(f"</{tag}>")
            if tag == "table":
                self.table_depth -= 1
                if self.table_depth == 0:
                    if self.table_nested or self.table_span:
                        self.stats["warnings"].append("HTML 表格含跨行/跨列/嵌套表格，已原样内嵌 HTML 保真")
                        self.out.append("\n" + "".join(self.table_raw) + "\n")
                    else:
                        gfm = self.tbl_model.to_gfm()
                        if gfm:
                            self.out.append("\n" + gfm + "\n")
                    self.stats["tables"] += 1
            elif tag in ("td", "th") and self.cell_buf is not None:
                rs, cs, is_h = self.cell_meta
                self.tbl_model.add_cell(Cell("".join(self.cell_buf).strip(), rs, cs, is_h))
                self.cell_buf, self.cell_meta = None, None
            return

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self.heading is not None:
            level, buf = self.heading
            text = "".join(buf).strip()
            if text:
                self._emit(self._prefix() + "#" * level + " " + text)
                self.stats["text_chars"] += len(text)
                if level == 1 and self.first_h1 is None:
                    self.first_h1 = text
            self.heading = None
        elif tag == "li" and self.li_buf is not None:
            text = "".join(self.li_buf).strip()
            marker = "-"
            if self.list_stack:
                top = self.list_stack[-1]
                top[1] += 1
                marker = f"{top[1]}." if top[0] == "ol" else "-"
            indent = "  " * max(0, len(self.list_stack) - 1)
            if text:
                lines = text.split("\n")
                block = "\n".join([f"{indent}{marker} {lines[0].strip()}"] +
                                  [f"{indent}  {l.strip()}" for l in lines[1:] if l.strip()])
                self.out.append("\n" + block + "\n")
                self.stats["text_chars"] += len(text)
            self.li_buf = None
        elif tag in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
        elif tag == "blockquote":
            self.flush_para()
            self.quote_depth = max(0, self.quote_depth - 1)
        elif tag == "a":
            if self.link_stack:
                href, buf, mark = self.link_stack.pop()
                if buf is not None and mark < len(buf):
                    text = "".join(buf[mark:]).strip()
                    if href and text:
                        buf[mark:] = [f"[{text}]({href})"]
        elif tag in BLOCK_TAGS:
            self.flush_para()

    def handle_data(self, data):
        if self.in_title:
            self.pending_title += data
            return
        if self.skip_depth:
            return
        if self.pre_depth:
            self.pre_buf.append(data)
            return
        collapsed = re.sub(r"[ \t\r\n]+", " ", data)
        if self.table_depth:
            self._echo(_html.escape(collapsed, quote=False))
            if self.cell_buf is not None:
                self.cell_buf.append(collapsed)
            return
        buf = self._buf()
        if buf is not None:
            buf.append(collapsed)

    def result(self) -> str:
        self.flush_para()
        header = ""
        if self.title and self.title != self.first_h1:
            header = f"# {self.title}\n"
        return header + "".join(self.out)


def parse_html(src: Path, md_path: Path, store: ImageStore, stats: dict) -> None:
    raw = src.read_bytes()
    encoding = "utf-8"
    if raw.startswith(b"\xef\xbb\xbf"):
        encoding, raw = "utf-8-sig", raw[3:]
    elif raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        encoding = "utf-16"
    else:
        m = re.search(rb'charset=["\']?([\w-]+)', raw[:4096], re.I)
        if m:
            encoding = m.group(1).decode("ascii", "ignore")
    try:
        text = raw.decode(encoding)
    except (UnicodeDecodeError, LookupError):
        try:
            text = raw.decode("gb18030")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", "replace")
            stats["warnings"].append("编码探测失败，按 utf-8 容错解码")

    conv = HtmlToMd(store, f"images/{md_path.stem}/", src.parent, stats)
    conv.feed(text)
    conv.close()
    md_path.write_text(conv.result(), encoding="utf-8")
    stats["backend"] = "html-stdlib"


# ─── DOC（转换链：soffice → WPS/Word COM → 指引）───────────────────────

SOFFICE_CANDIDATES = [
    "soffice",
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
]
WPS_PROGIDS = ("KWPS.Application", "wps.Application", "Word.Application")


def _find_soffice():
    for cand in SOFFICE_CANDIDATES:
        found = shutil.which(cand) or (cand if os.path.isfile(cand) else None)
        if found:
            return found
    return None


def doc_to_docx(src: Path, out_dir: Path):
    conv_dir = out_dir / ".converted"
    conv_dir.mkdir(parents=True, exist_ok=True)
    dst = conv_dir / (src.stem + ".docx")
    if dst.exists():
        return dst, "cached"

    soffice = _find_soffice()
    if soffice:
        try:
            subprocess.run(
                [soffice, "--headless", "--convert-to", "docx", "--outdir", str(conv_dir), str(src)],
                capture_output=True, timeout=300, check=True)
            if dst.exists():
                return dst, "soffice"
        except Exception as e:
            log.info("soffice 转换失败: %s", e)

    try:
        import pythoncom
        import win32com.client
    except ImportError:
        return None, None
    pythoncom.CoInitialize()
    app = None
    try:
        for progid in WPS_PROGIDS:
            try:
                app = win32com.client.DispatchEx(progid)
                used = progid
                break
            except Exception:
                continue
        else:
            return None, None
        app.Visible = False
        try:
            app.DisplayAlerts = 0
        except Exception:
            pass
        doc = app.Documents.Open(os.path.abspath(str(src)), ReadOnly=True)
        doc.SaveAs2(os.path.abspath(str(dst)), FileFormat=12)  # 12 = wdFormatXMLDocument
        doc.Close(False)
        if dst.exists():
            return dst, f"com:{used}"
        return None, None
    except Exception as e:
        log.info("COM 转换失败: %s", e)
        return None, None
    finally:
        if app is not None:
            try:
                app.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()


def parse_doc(src: Path, md_path: Path, store: ImageStore, stats: dict) -> None:
    converted, how = doc_to_docx(src, md_path.parent)
    if not converted:
        stats["status"] = "failed"
        stats["error"] = ("本机无 LibreOffice/WPS/Word 可自动转换 .doc。"
                          "请用 WPS 或 Word 打开后另存为 .docx，再重跑本脚本。")
        return
    stats["converted_via"] = how
    parse_docx(converted, md_path, store, stats)
    stats["format"] = "doc→docx"
    stats["backend"] = f"doc-convert({how})+docx-stdlib"


# ─── 调度与入口 ─────────────────────────────────────────────────────────

PARSERS = {
    "pdf": parse_pdf,
    "docx": parse_docx,
    "doc": parse_doc,
    "xlsx": parse_xlsx,
    "xls": parse_xls,
    "html": parse_html,
    "htm": parse_html,
}


def resolve_parser(path: Path, stats: dict):
    """按扩展名 + 魔数嗅探选解析器；不符时按实际格式走并给 warning。"""
    ext = path.suffix.lower().lstrip(".")
    sniffed = sniff_format(path)
    fmt = ext if ext in PARSERS else None
    if sniffed == "zip":
        real = "docx" if ext in ("doc", "docx") else ("xlsx" if ext in ("xls", "xlsx") else None)
        if ext == "doc" and real == "docx":
            stats["warnings"].append("扩展名 .doc 实际是 docx（zip）格式，按 docx 解析")
        elif ext == "xls" and real == "xlsx":
            stats["warnings"].append("扩展名 .xls 实际是 xlsx（zip）格式，按 xlsx 解析")
        fmt = real or fmt
    elif sniffed == "ole":
        real = "doc" if ext in ("doc", "docx") else ("xls" if ext in ("xls", "xlsx") else None)
        if ext == "docx":
            stats["warnings"].append("扩展名 .docx 实际是 .doc（OLE）格式，按 doc 解析")
        elif ext == "xlsx":
            stats["warnings"].append("扩展名 .xlsx 实际是 .xls（OLE）格式，按 xls 解析")
        fmt = real or fmt
    elif sniffed == "html" and ext in ("doc", "docx"):
        stats["warnings"].append(f"扩展名 .{ext} 实际是 HTML，按 HTML 解析")
        fmt = "html"
    elif sniffed == "pdf" and ext != "pdf":
        stats["warnings"].append(f"扩展名 .{ext} 实际是 PDF，按 PDF 解析")
        fmt = "pdf"
    return fmt


def collect_sources(target: Path):
    if target.is_file():
        return [target]
    out = []
    for p in sorted(target.rglob("*")):
        if not p.is_file():
            continue
        if "parsed" in p.parts:
            continue
        if p.name.startswith(SKIP_PREFIXES):
            continue
        if p.suffix.lower() in SUPPORTED_EXTS:
            out.append(p)
    return out


def load_old_manifest(out_dir: Path) -> dict:
    mf = out_dir / "manifest.json"
    if mf.is_file():
        try:
            return json.loads(mf.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(
        description="PRD 原始文档 1:1 解析（pdf/doc/docx/xlsx/xls/html → Markdown）")
    parser.add_argument("target", help="PRD 目录或单个文档文件")
    parser.add_argument("--out", help="输出目录（默认 <源目录>/parsed/）", default=None)
    parser.add_argument("--force", action="store_true", help="忽略 mtime 增量，强制重解析")
    parser.add_argument("--json", action="store_true", help="stdout 输出 manifest JSON")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        stream=sys.stderr, level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s")

    target = Path(args.target)
    if not target.exists():
        print(f"错误：目标不存在 {target}", file=sys.stderr)
        return 2
    sources = collect_sources(target)
    if not sources:
        print(f"错误：{target} 下未找到可解析文档（支持 {' '.join(sorted(SUPPORTED_EXTS))}）",
              file=sys.stderr)
        return 2

    out_dir = Path(args.out) if args.out else (target if target.is_dir() else target.parent) / "parsed"
    out_dir.mkdir(parents=True, exist_ok=True)
    old = {f.get("source"): f for f in load_old_manifest(out_dir).get("files", [])}

    stems = [sanitize_stem(p.stem) for p in sources]
    dup = {s for s in stems if stems.count(s) > 1}

    results = []
    for src, stem in zip(sources, stems):
        name = f"{stem}.{src.suffix.lstrip('.').lower()}.md" if stem in dup else f"{stem}.md"
        entry = {
            "source": src.name, "source_path": str(src),
            "format": src.suffix.lower().lstrip("."),
            "backend": None, "status": "ok", "output": f"parsed/{name}",
            "images_dir": f"parsed/images/{Path(name).stem}/",
            "text_chars": 0, "tables": 0, "images": 0, "warnings": [],
        }
        t0 = time.time()
        md_path = out_dir / name
        fmt = None
        try:
            if md_path.exists() and not args.force and md_path.stat().st_mtime >= src.stat().st_mtime:
                entry["status"] = "skipped"
                prior = old.get(src.name, {})
                for k in ("backend", "format", "text_chars", "tables", "images",
                          "warnings", "pages", "sheets", "converted_via"):
                    if k in prior:
                        entry[k] = prior[k]
                log.info("跳过（已解析且未变更）: %s", src.name)
                results.append(entry)
                continue

            fmt = resolve_parser(src, entry)
            if fmt not in PARSERS:
                entry["status"] = "failed"
                entry["error"] = f"无法确定解析方式（扩展名 {src.suffix}，魔数 {sniff_format(src)}）"
            else:
                entry["format"] = fmt
                store = ImageStore(out_dir / "images" / Path(name).stem)
                # pymupdf 会往 stdout 打杂音，别污染 --json 输出
                with contextlib.redirect_stdout(sys.stderr):
                    PARSERS[fmt](src, md_path, store, entry)
                if entry.get("status") != "failed":
                    entry["status"] = "warning" if entry["warnings"] else "ok"
        except ImportError as e:
            entry["status"] = "failed"
            pkg = "pymupdf" if fmt == "pdf" else "xlrd"
            entry["error"] = (f"缺少依赖 {e.name}。安装：\"{sys.executable}\" -m pip install {pkg} "
                              f"（国内镜像加 -i https://pypi.tuna.tsinghua.edu.cn/simple）")
        except Exception as e:
            entry["status"] = "failed"
            entry["error"] = f"{type(e).__name__}: {e}"
            log.exception("解析失败: %s", src.name)
        entry["elapsed_ms"] = int((time.time() - t0) * 1000)
        log.info("%s → %s [%s] text=%d tables=%d images=%d warnings=%d (%dms)",
                 src.name, entry["output"], entry["status"], entry["text_chars"],
                 entry["tables"], entry["images"], len(entry["warnings"]), entry["elapsed_ms"])
        results.append(entry)

    summary = {
        "ok": sum(1 for r in results if r["status"] == "ok"),
        "warning": sum(1 for r in results if r["status"] == "warning"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "skipped": sum(1 for r in results if r["status"] == "skipped"),
    }
    manifest = {
        "tool": "prd-parse", "tool_version": "1.0",
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "source_dir": str(target if target.is_dir() else target.parent),
        "files": results, "summary": summary,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
    else:
        for r in results:
            flag = {"ok": "✓", "warning": "△", "failed": "✗", "skipped": "⏭"}[r["status"]]
            line = f"{flag} {r['source']} → {r['output']} [{r['status']}]"
            if r["status"] != "skipped":
                line += f" text={r['text_chars']} tables={r['tables']} images={r['images']}"
            print(line)
            for w in r["warnings"][:5]:
                print(f"    △ {w}")
            if r["status"] == "failed":
                print(f"    ✗ {r.get('error', '')}")
        print(f"manifest: {out_dir / 'manifest.json'}")
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
