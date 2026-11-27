#!/usr/bin/env python3
"""Shared bilingual report builder for the Lottery Scheduling exercise series.

Builds, from one Markdown source per language:

* ``<stem>.pdf``  — A4 PDF laid out with ReportLab (two-pass, real TOC page
  numbers, PDF bookmarks, footer page numbers);
* ``<stem>.docx`` — Word document laid out with python-docx using the same
  page geometry and fixed line spacing, with an up front static table of
  contents filled from the PDF build so the Word file is complete on open.

Persian text is shaped with arabic-reshaper and ordered with python-bidi for
the PDF renderer; the DOCX relies on Word's native complex-script handling
(bidi paragraphs, rtl runs, Vazirmatn font).

Usage::

    python tools/report_build.py fa path/to/REPORT_FA.md out/REPORT_FA
    python tools/report_build.py en path/to/REPORT_EN.md out/REPORT_EN

The builder validates a configurable minimum page count (REPORT_MIN_PAGES;
default 41), so short reports cannot silently pass a strict build.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import arabic_reshaper
from PIL import Image as PILImage
from bidi.algorithm import get_display

# --------------------------------------------------------------------------
# Fonts
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "assets" / "fonts"

FA_REG = "Vazirmatn"
FA_BOLD = "Vazirmatn-Bold"
FA_MED = "Vazirmatn-Medium"
FA_SEMI = "Vazirmatn-SemiBold"
EN_REG = "DejaVuSerif"
EN_BOLD = "DejaVuSerif-Bold"
EN_IT = "DejaVuSerif-Italic"
EN_BOLDIT = "DejaVuSerif-BoldItalic"
MONO = "DejaVuSansMono"
MONO_BOLD = "DejaVuSansMono-Bold"

ARABIC = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY  # noqa: E402
from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph,  # noqa: E402
                                Spacer, Image, Table, TableStyle, PageBreak,
                                KeepTogether, HRFlowable, CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents  # noqa: E402
from reportlab.platypus.flowables import Flowable  # noqa: E402


def register_fonts():
    font_map = {
        FA_REG: "Vazirmatn-Regular.ttf", FA_BOLD: "Vazirmatn-Bold.ttf",
        FA_MED: "Vazirmatn-Medium.ttf", FA_SEMI: "Vazirmatn-SemiBold.ttf",
        EN_REG: "DejaVuSerif.ttf", EN_BOLD: "DejaVuSerif-Bold.ttf",
        EN_IT: "DejaVuSerif-Italic.ttf", EN_BOLDIT: "DejaVuSerif-BoldItalic.ttf",
        MONO: "DejaVuSansMono.ttf", MONO_BOLD: "DejaVuSansMono-Bold.ttf",
    }
    for name, fname in font_map.items():
        path = FONTS / fname
        if not path.is_file():
            raise FileNotFoundError(f"missing font {path}")
        try:
            pdfmetrics.registerFont(TTFont(name, str(path)))
        except Exception:
            pass  # already registered
    pdfmetrics.registerFontFamily(EN_REG, normal=EN_REG, bold=EN_BOLD, italic=EN_IT, boldItalic=EN_BOLDIT)
    pdfmetrics.registerFontFamily(FA_REG, normal=FA_REG, bold=FA_BOLD, italic=FA_REG, boldItalic=FA_BOLD)


# --------------------------------------------------------------------------
# Front matter + block parsing
# --------------------------------------------------------------------------

def parse_front_matter(text: str):
    meta = {"title": "Lottery Scheduling", "subtitle": "", "author": "kaspian021",
            "subject": "Operating Systems", "footer": "Lottery Scheduling"}
    body = text
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            chunk = text[4:end]
            for line in chunk.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip().lower()] = v.strip()
            body = text[end + 5:]
    return meta, body


H_RE = re.compile(r"^(#{1,4})\s+(.*)$")
TABLE_SEP = re.compile(r"^\|?\s*:?-{2,}")


def parse_blocks(body: str):
    lines = body.splitlines()
    blocks = []
    i = 0
    n = len(lines)
    while i < n:
        raw = lines[i]
        s = raw.rstrip()
        stripped = s.strip()
        if not stripped:
            i += 1
            continue
        if stripped == "[[PAGEBREAK]]":
            blocks.append(("pagebreak", None))
            i += 1
            continue
        if stripped.startswith("```"):
            j = i + 1
            code_lines = []
            while j < n and not lines[j].strip().startswith("```"):
                code_lines.append(lines[j].rstrip("\n"))
                j += 1
            blocks.append(("code", code_lines))
            i = j + 1
            continue
        m = H_RE.match(stripped)
        if m:
            level = len(m.group(1))
            blocks.append((f"h{min(level, 3)}", m.group(2).strip()))
            i += 1
            continue
        if stripped.startswith("|"):
            j = i
            rows = []
            while j < n and lines[j].strip().startswith("|"):
                rows.append(lines[j].strip())
                j += 1
            parsed = []
            for r in rows:
                cells = [c.strip() for c in r.strip().strip("|").split("|")]
                if len(cells) and TABLE_SEP.match(cells[0].replace("|", "").replace(" ", "")[:4] or "---"):
                    if all(set(c) <= set(":- ") for c in cells):
                        continue
                compact = [c for c in cells]
                if compact and all(set(c) <= set(":- ") for c in compact):
                    continue
                parsed.append(compact)
            if parsed:
                blocks.append(("table", parsed))
            i = j
            continue
        img = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", stripped)
        if img:
            blocks.append(("image", (img.group(1), img.group(2))))
            i += 1
            continue
        if stripped in ("---", "***", "___"):
            blocks.append(("hr", None))
            i += 1
            continue
        if stripped.startswith(("- ", "* ")):
            items = []
            j = i
            while j < n and lines[j].strip().startswith(("- ", "* ")):
                items.append(lines[j].strip()[2:].strip())
                j += 1
            blocks.append(("ul", items))
            i = j
            continue
        if re.match(r"^\d+\.\s", stripped):
            items = []
            j = i
            while j < n and re.match(r"^\d+\.\s", lines[j].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[j].strip()))
                j += 1
            blocks.append(("ol", items))
            i = j
            continue
        # paragraph: gather until blank line or another block start
        j = i
        buf = []
        while j < n:
            t = lines[j].strip()
            if not t:
                break
            if H_RE.match(t) or t.startswith("```") or t.startswith("|") or t.startswith("!["):
                break
            if t.startswith(("- ", "* ")) and buf:
                break
            buf.append(t)
            j += 1
        blocks.append(("p", " ".join(buf)))
        i = j
    return blocks


INLINE = re.compile(r"(\*\*.+?\*\*|`.+?`|\*[^*\n]+?\*|\[[^\]]+\]\([^)]+\))")


def split_inline(text: str):
    """Yield (segment_text, style) where style in plain,bold,italic,code,link."""
    pos = 0
    for m in INLINE.finditer(text):
        if m.start() > pos:
            yield text[pos:m.start()], "plain"
        t = m.group()
        if t.startswith("**"):
            yield t[2:-2], "bold"
        elif t.startswith("`"):
            yield t[1:-1], "code"
        elif t.startswith("["):
            mm = re.match(r"\[([^\]]+)\]\(([^)]+)\)", t)
            yield mm.group(1), "link"
        else:
            yield t[1:-1], "italic"
        pos = m.end()
    if pos < len(text):
        yield text[pos:], "plain"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def shape(s: str, rtl: bool) -> str:
    if not rtl:
        return s
    # Explicit RTL base direction is essential for runs that begin with a
    # Latin identifier inside an otherwise Persian paragraph.
    return get_display(arabic_reshaper.reshape(s), base_dir="R")


def inline_markup(text: str, rtl: bool, base_size: float):
    """Return ReportLab XML with Persian inline runs in visual (RTL) order.

    Markdown runs are kept intact for styling. ReportLab lays text out from
    left to right and does not perform paragraph-level bidi, so RTL paragraphs
    must emit runs in reverse order while each Persian run is shaped with an
    explicit RTL base direction. Code runs remain LTR and are never reshaped.
    """
    out = []
    runs = list(split_inline(text))
    if rtl:
        runs.reverse()
    for seg, style in runs:
        if not seg:
            continue
        raw = esc(seg)
        if style == "code":
            out.append(f'<font face="{MONO}" size="{base_size - 1.5:.1f}" color="#333333">{raw}</font>')
            continue
        shaped = esc(shape(seg, rtl))
        if style == "bold":
            out.append(f"<b>{shaped}</b>")
        elif style == "italic":
            out.append(f"<i>{shaped}</i>")
        elif style == "link":
            out.append(f'<font color="#1F4E79"><u>{shaped}</u></font>')
        else:
            out.append(shaped)
    return "".join(out)


# --------------------------------------------------------------------------
# Shared palette
# --------------------------------------------------------------------------
NAVY = colors.HexColor("#1F3864")
STEEL = colors.HexColor("#2F5496")
HEADER_BG = colors.HexColor("#DCE6F1")
CODE_BG = colors.HexColor("#F2F2F2")
GRAY = colors.HexColor("#595959")
LIGHT = colors.HexColor("#A6B8D4")


def pdf_styles(lang: str):
    rtl = lang == "fa"
    reg = FA_REG if rtl else EN_REG
    body_size = 11
    leading = 16.6
    align = TA_RIGHT if rtl else TA_JUSTIFY
    styles = {}
    styles["body"] = ParagraphStyle("body", fontName=reg, fontSize=body_size, leading=leading,
                                    alignment=align, textColor=colors.black,
                                    spaceAfter=5, spaceBefore=0)
    styles["body_caption"] = ParagraphStyle("body_caption", parent=styles["body"], fontSize=8.5,
                                            leading=11.5, alignment=TA_CENTER,
                                            textColor=GRAY, spaceBefore=2, spaceAfter=7)
    styles["h1"] = ParagraphStyle("h1", fontName=(FA_BOLD if rtl else EN_BOLD), fontSize=16.5,
                                  leading=21, alignment=align, textColor=NAVY,
                                  spaceBefore=14, spaceAfter=6, keepWithNext=1)
    styles["h2"] = ParagraphStyle("h2", fontName=(FA_BOLD if rtl else EN_BOLD), fontSize=13,
                                  leading=17, alignment=align, textColor=STEEL,
                                  spaceBefore=10, spaceAfter=4, keepWithNext=1)
    styles["h3"] = ParagraphStyle("h3", fontName=(FA_BOLD if rtl else EN_BOLD), fontSize=11.5,
                                  leading=15, alignment=align, textColor=colors.black,
                                  spaceBefore=8, spaceAfter=3, keepWithNext=1)
    styles["bullet"] = ParagraphStyle("bullet", parent=styles["body"],
                                      leftIndent=0 if rtl else 14,
                                      rightIndent=14 if rtl else 0,
                                      firstLineIndent=0)
    styles["code"] = ParagraphStyle("code", fontName=MONO, fontSize=8.2, leading=10.6,
                                    alignment=TA_LEFT, textColor=colors.HexColor("#1a1a1a"),
                                    backColor=CODE_BG, borderPadding=(4, 6, 4, 6),
                                    borderColor=colors.HexColor("#D0D0D0"), borderWidth=0.4,
                                    spaceAfter=2)
    styles["cell"] = ParagraphStyle("cell", fontName=reg, fontSize=8.6, leading=11.4,
                                    alignment=(TA_RIGHT if rtl else TA_LEFT), spaceAfter=0)
    styles["cell_head"] = ParagraphStyle("cell_head", parent=styles["cell"],
                                         fontName=(FA_BOLD if rtl else EN_BOLD),
                                         textColor=NAVY)
    styles["cover_title"] = ParagraphStyle("cover_title", fontName=(FA_BOLD if rtl else EN_BOLD),
                                           fontSize=25, leading=31, alignment=TA_CENTER,
                                           textColor=NAVY, spaceAfter=10)
    styles["cover_sub"] = ParagraphStyle("cover_sub", fontName=reg, fontSize=13.5, leading=19,
                                         alignment=TA_CENTER, textColor=STEEL, spaceAfter=6)
    styles["cover_note"] = ParagraphStyle("cover_note", fontName=reg, fontSize=10, leading=16,
                                          alignment=TA_CENTER, textColor=GRAY)
    styles["toc1"] = ParagraphStyle("toc1", fontName=(FA_BOLD if rtl else EN_BOLD), fontSize=10.5,
                                    leading=15, alignment=(TA_RIGHT if rtl else TA_LEFT),
                                    textColor=NAVY)
    styles["toc2"] = ParagraphStyle("toc2", fontName=reg, fontSize=9.5, leading=13.2,
                                    leftIndent=(0 if rtl else 16), rightIndent=(16 if rtl else 0),
                                    alignment=(TA_RIGHT if rtl else TA_LEFT))
    styles["toc_head"] = ParagraphStyle("toc_head", fontName=(FA_BOLD if rtl else EN_BOLD),
                                        fontSize=16.5, leading=22, alignment=TA_CENTER,
                                        textColor=NAVY, spaceAfter=10)
    return styles, rtl, reg



class StaticTOC(Flowable):
    """One page of a precomputed table of contents (deterministic across builds).

    ``entries`` is a slice of (level, text, page) or ``None`` on the first,
    measurement pass (nothing is drawn but the frame height is identical).
    """

    def __init__(self, entries, lang, title_gap=70.0):
        super().__init__()
        self.entries = entries or []
        self.empty = entries is None
        self.lang = lang
        self.title_gap = title_gap
        self.leading = 13.6 if lang == "fa" else 13.0

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        self.height = availHeight - self.title_gap
        return self.width, self.height

    def max_lines(self):
        return int((self.height - 8) // self.leading)

    def draw(self):
        if self.empty:
            return
        c = self.canv
        rtl = self.lang == "fa"
        reg = FA_REG if rtl else EN_REG
        bold = FA_BOLD if rtl else EN_BOLD
        y = self.height - 6
        dot_font, dot_size = reg, 9
        dot_w = pdfmetrics.stringWidth(".", dot_font, dot_size)
        for level, text, page in self.entries:
            size = 10 if level == 1 else 8.6
            font = bold if level == 1 else reg
            plain = re.sub(r"[*`]", "", str(text))
            max_title = self.width - 58
            # shrink-to-fit: truncate overly long titles
            if pdfmetrics.stringWidth(plain, font, size) > max_title:
                while plain and pdfmetrics.stringWidth(plain + "…", font, size) > max_title:
                    plain = plain[:-1]
                plain = plain + "…"
            shaped = _shapen(plain, rtl) if rtl else plain
            c.setFillColor(NAVY if level == 1 else colors.HexColor("#262626"))
            c.setFont(font, size)
            page_str = str(page)
            pw = pdfmetrics.stringWidth(page_str, reg, 9)
            if rtl:
                title_x = self.width  # right aligned
                page_x = 0
                c.drawRightString(title_x, y, shaped)
                c.drawString(page_x, y, page_str)
                title_w = pdfmetrics.stringWidth(shaped, font, size)
                dots_from = pw + 6
                dots_to = self.width - title_w - 6
            else:
                c.drawString(0, y, shaped)
                c.drawRightString(self.width, y, page_str)
                title_w = pdfmetrics.stringWidth(shaped, font, size)
                dots_from = title_w + 6
                dots_to = self.width - pw - 6
            # dotted leader
            c.setFillColor(colors.HexColor("#9DB2CE"))
            c.setFont(dot_font, dot_size)
            if dots_to > dots_from:
                n_dots = int((dots_to - dots_from) / (dot_w * 1.18))
                if n_dots > 0:
                    c.drawString(dots_from, y, "." * n_dots)
            y -= self.leading


def pml(text, styles, rtl, kind="body", base_size=11):
    return Paragraph(inline_markup(text, rtl, base_size), styles[kind])


# --------------------------------------------------------------------------
# PDF document template with header/footer + TOC hooks
# --------------------------------------------------------------------------

def _shapen(s: str, rtl: bool) -> str:
    return get_display(arabic_reshaper.reshape(s), base_dir="R") if rtl else s


class ReportDoc(BaseDocTemplate):
    def __init__(self, filename, lang, meta, **kw):
        super().__init__(filename, pagesize=A4,
                         leftMargin=40, rightMargin=40,
                         topMargin=52, bottomMargin=48,
                         title=meta.get("title", "Lottery Scheduling"),
                         author=meta.get("author", "kaspian021"),
                         subject=meta.get("subject", "Operating Systems"))
        self.lang = lang
        self.meta = meta
        self.heading_pages: list[tuple[int, str, int]] = []  # (level, raw text, page)
        self._toc_seq = 0
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height,
                      id="main", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        cover = Frame(self.leftMargin, self.bottomMargin, self.width, self.height,
                      id="cover", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([PageTemplate(id="Cover", frames=[cover], onPage=self._cover_bg),
                               PageTemplate(id="Body", frames=[frame], onPage=self._body_deco)])

    # ---- page furniture ---------------------------------------------------
    def _cover_bg(self, canv, doc):
        canv.saveState()
        canv.setFillColor(colors.HexColor("#F7FAFE"))
        canv.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        # double frame
        canv.setStrokeColor(STEEL)
        canv.setLineWidth(2.4)
        canv.rect(18, 18, A4[0] - 36, A4[1] - 36, fill=0, stroke=1)
        canv.setLineWidth(0.7)
        canv.rect(24, 24, A4[0] - 48, A4[1] - 48, fill=0, stroke=1)
        # top accent ribbon
        canv.setFillColor(NAVY)
        canv.rect(18, A4[1] - 78, A4[0] - 36, 34, fill=1, stroke=0)
        canv.setFillColor(colors.white)
        canv.setFont(FA_BOLD if self.lang == "fa" else EN_BOLD, 9.5)
        kicker = "OPERATING SYSTEMS  ·  COURSE PROJECT  ·  2026" if self.lang == "en" else "سیستم عامل  ·  پروژه درس  ·  ۲۰۲۶"
        canv.drawCentredString(A4[0] / 2, A4[1] - 56, _shapen(kicker, self.lang == "fa"))
        canv.setFillColor(NAVY)
        canv.rect(18, 44, A4[0] - 36, 16, fill=1, stroke=0)
        canv.restoreState()

    def _body_deco(self, canv, doc):
        rtl = self.lang == "fa"
        reg = FA_REG if rtl else EN_REG
        canv.saveState()
        page_no = canv.getPageNumber()
        # header
        canv.setStrokeColor(LIGHT)
        canv.setLineWidth(0.6)
        canv.line(self.leftMargin, A4[1] - 38, A4[0] - self.rightMargin, A4[1] - 38)
        canv.setFillColor(GRAY)
        canv.setFont(reg, 7.5)
        header_txt = self.meta.get("footer", "Lottery Scheduling")
        if rtl:
            canv.drawRightString(A4[0] - self.rightMargin, A4[1] - 32, _shapen(header_txt, True))
            canv.setFont(EN_REG, 7.5)
            canv.drawString(self.leftMargin, A4[1] - 32, "kaspian021/Lottery_Scheduling")
        else:
            canv.drawString(self.leftMargin, A4[1] - 32, header_txt)
            canv.drawRightString(A4[0] - self.rightMargin, A4[1] - 32, "kaspian021/Lottery_Scheduling")
        # footer
        canv.setStrokeColor(LIGHT)
        canv.line(self.leftMargin, 34, A4[0] - self.rightMargin, 34)
        canv.setFillColor(GRAY)
        canv.setFont(reg, 9)
        canv.drawCentredString(A4[0] / 2, 22, f"— {page_no} —")
        canv.restoreState()

    def beforeDocument(self):
        self.heading_pages = []
        self._toc_seq = 0

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            style = flowable.style.name
            if style in ("h1", "h2", "h3"):
                level = int(style[1])
                text = getattr(flowable, "_raw_text", None)
                if text:
                    self._toc_seq += 1
                    key = f"toc-anchor-{self._toc_seq}"
                    rtl = self.lang == "fa"
                    self.canv.bookmarkPage(key)
                    self.canv.addOutlineEntry(text, key, level=level - 1, closed=(level > 1))
                    plain_text = re.sub(r"[*`]", "", text)
                    display_text = esc(_shapen(plain_text, rtl))
                    self.notify("TOCEntry", (level - 1, display_text, self.page, key))
                    self.heading_pages.append((level, text, self.page))


def build_pdf(lang: str, blocks, meta, out_pdf: str, toc_entries=None, n_toc_pages=1, toc_out=None):
    register_fonts()
    styles, rtl, reg = pdf_styles(lang)
    doc = ReportDoc(out_pdf, lang, meta)
    story = []

    # ---------- cover ----------
    story.append(Spacer(1, 64))
    story.append(HRFlowable(width="38%", thickness=2.2, color=STEEL, hAlign="CENTER", spaceAfter=18))
    story.append(Paragraph(inline_markup(meta["title"], rtl, 25), styles["cover_title"]))
    if meta.get("subtitle"):
        story.append(Paragraph(inline_markup(meta["subtitle"], rtl, 13.5), styles["cover_sub"]))
    story.append(HRFlowable(width="38%", thickness=2.2, color=STEEL, hAlign="CENTER", spaceBefore=6, spaceAfter=26))

    def cline(label, value):
        txt = f"**{label}** {value}" if lang == "en" else f"**{label}** {value}"
        return Paragraph(inline_markup(txt, rtl, 10.5), styles["cover_note"])

    repo_label = "Repository" if lang == "en" else "مخزن"
    branch_label = "Branch" if lang == "en" else "انشعاب"
    ex_label = "Deliverable" if lang == "en" else "تحویل"
    date_label = "Date" if lang == "en" else "تاریخ"
    story.append(cline(repo_label + ":", meta.get("repo", "kaspian021/Lottery_Scheduling")))
    story.append(cline(branch_label + ":", meta.get("branch", "arena/ce95d03c-lottery-scheduling")))
    story.append(cline(ex_label + ":", meta.get("deliverable", "")))
    story.append(cline(date_label + ":", meta.get("date", "2026-11-27")))
    story.append(Spacer(1, 120))
    if lang == "fa":
        blurb = "این گزارش بر پایه‌ی اجرای واقعی کد و سناریوهای همین تمرین تولید شده است؛ همه‌ی اعداد از خروجی شبیه‌ساز خوانده شده‌اند."
    else:
        blurb = ("This report is built from the actual execution of this exercise's code and scenarios; "
                 "every number quoted here is read from the simulator output in the repository.")
    story.append(Paragraph(inline_markup(blurb, rtl, 10), styles["cover_note"]))
    story.append(PageBreak())

    # ---------- table of contents ----------
    toc_title = "Table of Contents" if lang == "en" else "فهرست مطالب"
    story.append(Paragraph(shape(esc(toc_title), rtl), styles["toc_head"]))
    # split entries into fixed one-frame slices; pages must match across builds
    lead = 13.6 if lang == "fa" else 13.0
    frame_h = A4[1] - 52 - 48
    lines_per = int((frame_h - 70 - 8) // lead)
    if toc_entries is None:
        slices = [None] * n_toc_pages
    else:
        slices = [toc_entries[i:i + lines_per] for i in range(0, len(toc_entries), lines_per)] or [toc_entries]
    for idx, sl in enumerate(slices):
        if idx:
            story.append(PageBreak())
            if toc_title:
                story.append(Paragraph(shape(esc(("ادامه فهرست" if lang == "fa" else "Contents (continued)")), rtl), styles["toc_head"]))
        story.append(StaticTOC(sl, lang, title_gap=70))
    story.append(PageBreak())

    # ---------- body ----------
    from reportlab.platypus import NextPageTemplate
    story.insert(1, NextPageTemplate("Body"))

    def heading(level, text):
        st = styles[f"h{level}"]
        p = Paragraph(inline_markup(text, rtl, 13 if level == 2 else 16.5), st)
        p._raw_text = text
        return p

    def render_table(rows):
        ncols = max(len(r) for r in rows)
        norm = [r + [""] * (ncols - len(r)) for r in rows]
        if rtl:
            norm = [list(reversed(r)) for r in norm]
        data = []
        for ri, row in enumerate(norm):
            line = []
            for cell in row:
                st = styles["cell_head"] if ri == 0 else styles["cell"]
                line.append(Paragraph(inline_markup(cell, rtl, 8.6), st))
            data.append(line)
        widths = []
        for ci in range(ncols):
            maxlen = max(len(re.sub(r"[*`]", "", (r[ci] if ci < len(r) else ""))) for r in norm)
            widths.append(min(max(maxlen, 6), 40) ** 0.82)
        tot = sum(widths)
        col_w = [ (A4[0] - 80) * w / tot for w in widths ]
        t = Table(data, colWidths=col_w, repeatRows=1, hAlign="CENTER")
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, LIGHT),
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        return t

    def render_image(alt, rel_path, md_dir):
        candidates = [Path(rel_path)]
        if not Path(rel_path).is_absolute():
            candidates = [md_dir / rel_path, ROOT / rel_path.lstrip("./")]
        path = next((c for c in candidates if c.is_file()), None)
        if path is None:
            base = Path(rel_path).name
            for sub in ("diagrams", "docs/figures", "docs/generated", "assets", "output", "images", "."):
                c = ROOT / sub / base
                if c.is_file():
                    path = c
                    break
        if path is None:
            hits = [h for h in ROOT.rglob(Path(rel_path).name) if ".git" not in h.parts and ".venv" not in h.parts]
            if hits:
                path = hits[0]
        if path is None:
            raise FileNotFoundError(f"missing image {rel_path}")
        with PILImage.open(path) as im:
            w, h = im.size
        max_w, max_h = 6.05, 4.35
        scale = min(max_w / (w / 96.0), max_h / (h / 96.0))
        img = Image(str(path), width=(w / 96.0) * scale * 72.0, height=(h / 96.0) * scale * 72.0)
        img.hAlign = "CENTER"
        items = [img]
        if alt:
            items.append(Paragraph(inline_markup(alt, rtl, 8.5), styles["body_caption"]))
        return KeepTogether(items)

    for kind, payload in blocks:
        if kind == "h1":
            story.append(heading(1, payload))
        elif kind == "h2":
            story.append(heading(2, payload))
        elif kind == "h3":
            story.append(heading(3, payload))
        elif kind == "p":
            story.append(pml(payload, styles, rtl, "body", 11))
        elif kind == "ul":
            for item in payload:
                bullet = "•" if rtl else "•"
                txt = f"{inline_markup(item, rtl, 11)}"
                story.append(Paragraph(f"{bullet}&nbsp;&nbsp;{txt}", styles["bullet"]))
        elif kind == "ol":
            for idx, item in enumerate(payload, 1):
                story.append(Paragraph(f"{idx}.&nbsp;&nbsp;{inline_markup(item, rtl, 11)}", styles["bullet"]))
        elif kind == "table":
            story.append(render_table(payload))
            story.append(Spacer(1, 6))
        elif kind == "code":
            for line in payload:
                safe = esc(line if line else " ").replace("\t", "    ")
                story.append(Paragraph(safe, styles["code"]))
            story.append(Spacer(1, 7))
        elif kind == "image":
            story.append(render_image(payload[0], payload[1], Path(_MD_DIR)))
        elif kind == "pagebreak":
            story.append(PageBreak())
        elif kind == "hr":
            story.append(HRFlowable(width="100%", thickness=0.6, color=LIGHT, spaceBefore=6, spaceAfter=6))

    doc.multiBuild(story)
    return doc


def _escape_xml(s: str) -> str:
    return esc(s)


# --------------------------------------------------------------------------
# DOCX builder
# --------------------------------------------------------------------------

def build_docx(lang: str, blocks, meta, out_docx: str, toc_entries, md_dir: Path):
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Inches, Pt, RGBColor

    rtl = lang == "fa"
    REG = "Vazirmatn" if rtl else "DejaVu Serif"
    BOLD = "Vazirmatn" if rtl else "DejaVu Serif"  # bold via b flag
    MONO = "DejaVu Sans Mono"
    NAVY_HEX = "1F3864"
    STEEL_HEX = "2F5496"
    BODY_PT = 11
    LEAD_PT = 16.6

    def set_run_fonts(run, fontname, size=None, bold=None, color=None, rtl_run=None):
        rpr = run._element.get_or_add_rPr()
        fonts = rpr.find(qn("w:rFonts"))
        if fonts is None:
            fonts = OxmlElement("w:rFonts")
            rpr.append(fonts)
        for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            fonts.set(qn(attr), fontname)
        if size:
            run.font.size = Pt(size)
        if bold is not None:
            run.bold = bold
        if color:
            run.font.color.rgb = RGBColor.from_string(color)
        if rtl_run is None:
            # LTR identifiers, dates, paths and numerals must remain LTR even
            # when embedded in an RTL Persian paragraph.
            rtl_run = rtl and bool(ARABIC.search(run.text or ""))
        rpr2 = run._element.get_or_add_rPr()
        rtl_el = rpr2.find(qn("w:rtl"))
        if rtl_run:
            if rtl_el is None:
                rtl_el = OxmlElement("w:rtl")
                rpr2.append(rtl_el)
            rtl_el.set(qn("w:val"), "1")
        elif rtl_el is not None:
            rpr2.remove(rtl_el)

    def set_par(p, align=None, before=0, after=5, exact=LEAD_PT, rtl_par=None, keep_next=False):
        ppr = p._p.get_or_add_pPr()
        use_rtl = rtl if rtl_par is None else rtl_par
        bidi = ppr.find(qn("w:bidi"))
        if use_rtl:
            if bidi is None:
                bidi = OxmlElement("w:bidi")
                ppr.append(bidi)
            bidi.set(qn("w:val"), "1")
            if align is None:
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        else:
            if bidi is not None:
                ppr.remove(bidi)
            if align is None:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        if align == "center":
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf = p.paragraph_format
        pf.space_before = Pt(before)
        pf.space_after = Pt(after)
        pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        pf.line_spacing = Pt(exact)
        if keep_next:
            pf.keep_with_next = True

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.27), Inches(11.69)
    sec.top_margin, sec.bottom_margin = Inches(0.72), Inches(0.68)
    sec.left_margin, sec.right_margin = Inches(0.59), Inches(0.59)
    if rtl:
        # whole-document RTL: mirrors margins/headers/footers in Word and sets
        # the default paragraph direction to RTL (ECMA-376: bidi goes between
        # cols and docGrid)
        sectPr = sec._sectPr
        if sectPr.find(qn("w:bidi")) is None:
            bidi_el = OxmlElement("w:bidi")
            cols_el = sectPr.find(qn("w:cols"))
            if cols_el is not None:
                cols_el.addnext(bidi_el)
            else:
                sectPr.append(bidi_el)

    # default style
    normal = doc.styles["Normal"]
    normal.font.name = REG
    normal.font.size = Pt(BODY_PT)
    rfonts = normal.element.get_or_add_rPr().get_or_add_rFonts()
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), REG)

    # footer with page number
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if rtl:
        fpp = fp._p.get_or_add_pPr()
        if fpp.find(qn("w:bidi")) is None:
            fbidi = OxmlElement("w:bidi")
            fpp.append(fbidi)
    r = fp.add_run()
    set_run_fonts(r, REG, 9, rtl_run=False)
    from docx.oxml import OxmlElement as _OE
    b = _OE("w:fldChar"); b.set(qn("w:fldCharType"), "begin"); r._r.append(b)
    it = _OE("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = " PAGE "; r._r.append(it)
    e = _OE("w:fldChar"); e.set(qn("w:fldCharType"), "end"); r._r.append(e)

    def add_par(text_markup, style_kind="body", before=None, after=None, keep_next=False):
        p = doc.add_paragraph()
        exact = LEAD_PT
        if style_kind == "h1":
            set_par(p, before=14, after=6, exact=21, keep_next=True)
            color, size, bold = NAVY_HEX, 16.5, True
        elif style_kind == "h2":
            set_par(p, before=10, after=4, exact=17, keep_next=True)
            color, size, bold = STEEL_HEX, 13, True
        elif style_kind == "h3":
            set_par(p, before=8, after=3, exact=15, keep_next=True)
            color, size, bold = "000000", 11.5, True
        elif style_kind == "caption":
            set_par(p, align="center", before=2, after=7, exact=12)
            color, size, bold = "595959", 8.5, False
        else:
            set_par(p, before=before if before is not None else 0,
                    after=after if after is not None else 5, exact=exact)
            color, size, bold = "000000", BODY_PT, None
        for seg, style in split_inline(text_markup):
            if not seg:
                continue
            if style == "code":
                r = p.add_run(seg)
                set_run_fonts(r, MONO, BODY_PT - 1.5, color="333333", rtl_run=False)
                continue
            r = p.add_run(seg)
            if style == "bold":
                set_run_fonts(r, REG, size, bold=True, color=color)
            elif style == "italic":
                set_run_fonts(r, REG, size, bold=bold, color=color)
                r.italic = True
            elif style == "link":
                set_run_fonts(r, REG, size, bold=bold, color="1F4E79")
                r.underline = True
            else:
                set_run_fonts(r, REG, size, bold=bold, color=color)
        return p

    def add_code_block(lines):
        for idx, line in enumerate(lines):
            p = doc.add_paragraph()
            set_par(p, before=0, after=0, exact=11, rtl_par=False, keep_next=(len(lines) <= 20))
            ppr = p._p.get_or_add_pPr()
            shd = OxmlElement("w:shd")
            shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), "F2F2F2")
            ppr.append(shd)
            pf = p.paragraph_format
            pf.left_indent = Inches(0.16)
            pf.right_indent = Inches(0.16)
            r = p.add_run(line if line else " ")
            set_run_fonts(r, MONO, 8.2, rtl_run=False, color="1a1a1a")
        p = doc.add_paragraph()
        set_par(p, before=0, after=4, exact=6, rtl_par=False)

    def add_table(rows):
        ncols = max(len(r) for r in rows)
        # w:bidiVisual mirrors the visual cell order in Word. Keep the
        # logical Markdown order here; reversing it as well would mirror twice.
        norm = [r + [""] * (ncols - len(r)) for r in rows]
        widths = []
        for ci in range(ncols):
            maxlen = max(len(re.sub(r"[*`]", "", (r[ci] if ci < len(r) else ""))) for r in rows)
            widths.append(min(max(maxlen, 6), 40) ** 0.82)
        tot = sum(widths)
        table = doc.add_table(rows=len(norm), cols=ncols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        usable = 7.09
        tbl = table._tbl
        tblPr = tbl.tblPr
        layout = OxmlElement("w:tblLayout"); layout.set(qn("w:type"), "fixed"); tblPr.append(layout)
        if rtl:
            bidi_v = OxmlElement("w:bidiVisual"); bidi_v.set(qn("w:val"), "1"); tblPr.append(bidi_v)
        for ri, row in enumerate(norm):
            trPr = table.rows[ri]._tr.get_or_add_trPr()
            cant = OxmlElement("w:cantSplit"); trPr.append(cant)
            if ri == 0:
                th = OxmlElement("w:tblHeader"); trPr.append(th)
            for ci, cell in enumerate(row):
                c = table.cell(ri, ci)
                c.width = Inches(usable * widths[ci] / tot)
                p = c.paragraphs[0]
                set_par(p, before=1, after=1, exact=11.6)
                for seg, style in split_inline(cell):
                    if not seg:
                        continue
                    r = p.add_run(seg)
                    if ri == 0:
                        set_run_fonts(r, REG, 8.6, bold=True, color=NAVY_HEX)
                    elif style == "bold":
                        set_run_fonts(r, REG, 8.6, bold=True)
                    elif style == "code":
                        set_run_fonts(r, MONO, 7.4, rtl_run=False, color="333333")
                    else:
                        set_run_fonts(r, REG, 8.6)
                if ri == 0:
                    tcPr = c._tc.get_or_add_tcPr()
                    shd = OxmlElement("w:shd")
                    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), "DCE6F1")
                    tcPr.append(shd)
        p = doc.add_paragraph(); set_par(p, before=0, after=2, exact=5, rtl_par=False)

    def add_picture(alt, rel_path):
        candidates = [md_dir / rel_path, ROOT / rel_path.lstrip("./")]
        path = next((c for c in candidates if c.is_file()), None)
        if path is None:
            base = Path(rel_path).name
            for sub in ("diagrams", "docs/figures", "docs/generated", "assets", "output", "."):
                c = ROOT / sub / base
                if c.is_file():
                    path = c
                    break
        if path is None:
            raise FileNotFoundError(f"missing image {rel_path}")
        with PILImage.open(path) as im:
            w, h = im.size
        max_w, max_h = 6.05, 4.35
        scale = min(max_w / (w / 96.0), max_h / (h / 96.0))
        p = doc.add_paragraph()
        set_par(p, align="center", before=4, after=2, exact=int(h / 96.0 * scale * 72) + 8)
        p.add_run().add_picture(str(path), width=Inches(w / 96.0 * scale))
        if alt:
            add_par(alt, "caption")

    # ---------- cover ----------
    p = doc.add_paragraph(); set_par(p, align="center", before=30, after=4, exact=18)
    kicker = meta.get("kicker", "OPERATING SYSTEMS — COURSE PROJECT" if lang == "en" else "پروژه درس سیستم عامل")
    r = p.add_run(kicker); set_run_fonts(r, REG, 9, bold=True, color=STEEL_HEX)
    p = doc.add_paragraph(); set_par(p, align="center", before=0, after=16, exact=8, rtl_par=False)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr"); bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single"); bottom.set(qn("w:sz"), "14"); bottom.set(qn("w:space"), "1"); bottom.set(qn("w:color"), STEEL_HEX)
    pBdr.append(bottom); pPr.append(pBdr)

    p = doc.add_paragraph(); set_par(p, align="center", before=4, after=10, exact=33)
    for seg, style in split_inline(meta["title"]):
        if not seg:
            continue
        r = p.add_run(seg); set_run_fonts(r, REG, 25, bold=True, color=NAVY_HEX)
    if meta.get("subtitle"):
        p = doc.add_paragraph(); set_par(p, align="center", before=0, after=14, exact=20)
        for seg, style in split_inline(meta["subtitle"]):
            if not seg:
                continue
            r = p.add_run(seg); set_run_fonts(r, REG, 13.5, color=STEEL_HEX)

    def cover_line(label, value):
        p = doc.add_paragraph(); set_par(p, align="center", before=0, after=2, exact=17)
        r = p.add_run(label + " "); set_run_fonts(r, REG, 10.5, bold=True, color=NAVY_HEX)
        r = p.add_run(value); set_run_fonts(r, REG, 10.5, color="262626")

    repo_label = "Repository:" if lang == "en" else "مخزن:"
    branch_label = "Branch:" if lang == "en" else "انشعاب:"
    ex_label = "Deliverable:" if lang == "en" else "تحویل:"
    date_label = "Date:" if lang == "en" else "تاریخ:"
    cover_line(repo_label, meta.get("repo", "kaspian021/Lottery_Scheduling"))
    cover_line(branch_label, meta.get("branch", "arena/ce95d03c-lottery-scheduling"))
    cover_line(ex_label, meta.get("deliverable", ""))
    cover_line(date_label, meta.get("date", "2026-11-27"))
    p = doc.add_paragraph(); set_par(p, before=0, after=0, exact=100)
    p = doc.add_paragraph(); set_par(p, align="center", before=0, after=0, exact=16)
    blurb = ("This report is built from the actual execution of this exercise's code and scenarios."
             if lang == "en" else
             "این گزارش بر پایه‌ی اجرای واقعی کد و سناریوهای همین تمرین تولید شده است.")
    r = p.add_run(blurb); set_run_fonts(r, REG, 9.5, color="595959")
    doc.add_page_break()

    # ---------- static TOC ----------
    p = doc.add_paragraph(); set_par(p, align="center", before=6, after=12, exact=26)
    toc_title = "Table of Contents" if lang == "en" else "فهرست مطالب"
    r = p.add_run(toc_title); set_run_fonts(r, REG, 17, bold=True, color=NAVY_HEX)

    entries = toc_entries  # list of (level, text, page)
    from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
    for level, text, page in entries:
        p = doc.add_paragraph()
        set_par(p, before=1.5, after=1.5, exact=(15.5 if level == 1 else 13.2), rtl_par=rtl)
        pf = p.paragraph_format
        if level >= 2:
            if rtl:
                pf.right_indent = Inches(0.28)
            else:
                pf.left_indent = Inches(0.28)
        pf.tab_stops.add_tab_stop(Inches(6.9), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        r = p.add_run(re.sub(r"[*`]", "", text))
        set_run_fonts(r, REG, 10 if level == 1 else 9, bold=(level == 1),
                      color=(NAVY_HEX if level == 1 else "262626"))
        r = p.add_run("\t"); set_run_fonts(r, REG, 9)
        r = p.add_run(str(page)); set_run_fonts(r, REG, 9, color="262626")
    doc.add_page_break()

    # ---------- body ----------
    for kind, payload in blocks:
        if kind == "h1":
            add_par(payload, "h1")
        elif kind == "h2":
            add_par(payload, "h2")
        elif kind == "h3":
            add_par(payload, "h3")
        elif kind == "p":
            add_par(payload, "body")
        elif kind == "ul":
            for item in payload:
                p = doc.add_paragraph()
                set_par(p, before=0, after=2.5, exact=LEAD_PT)
                pf = p.paragraph_format
                if rtl:
                    pf.right_indent = Inches(0.22)
                else:
                    pf.left_indent = Inches(0.22)
                r = p.add_run("•  "); set_run_fonts(r, REG, BODY_PT, color=STEEL_HEX, bold=True, rtl_run=rtl)
                for seg, style in split_inline(item):
                    if not seg:
                        continue
                    if style == "code":
                        rr = p.add_run(seg); set_run_fonts(rr, MONO, BODY_PT - 1.5, rtl_run=False, color="333333")
                    elif style == "bold":
                        rr = p.add_run(seg); set_run_fonts(rr, REG, BODY_PT, bold=True)
                    elif style == "italic":
                        rr = p.add_run(seg); set_run_fonts(rr, REG, BODY_PT); rr.italic = True
                    elif style == "link":
                        rr = p.add_run(seg); set_run_fonts(rr, REG, BODY_PT, color="1F4E79"); rr.underline = True
                    else:
                        rr = p.add_run(seg); set_run_fonts(rr, REG, BODY_PT)
        elif kind == "ol":
            for idx, item in enumerate(payload, 1):
                p = doc.add_paragraph()
                set_par(p, before=0, after=2.5, exact=LEAD_PT)
                pf = p.paragraph_format
                if rtl:
                    pf.right_indent = Inches(0.22)
                else:
                    pf.left_indent = Inches(0.22)
                r = p.add_run(f"{idx}.  "); set_run_fonts(r, REG, BODY_PT, color=STEEL_HEX, bold=True, rtl_run=rtl)
                for seg, style in split_inline(item):
                    if not seg:
                        continue
                    if style == "code":
                        rr = p.add_run(seg); set_run_fonts(rr, MONO, BODY_PT - 1.5, rtl_run=False, color="333333")
                    elif style == "bold":
                        rr = p.add_run(seg); set_run_fonts(rr, REG, BODY_PT, bold=True)
                    elif style == "italic":
                        rr = p.add_run(seg); set_run_fonts(rr, REG, BODY_PT); rr.italic = True
                    elif style == "link":
                        rr = p.add_run(seg); set_run_fonts(rr, REG, BODY_PT, color="1F4E79"); rr.underline = True
                    else:
                        rr = p.add_run(seg); set_run_fonts(rr, REG, BODY_PT)
        elif kind == "table":
            add_table(payload)
        elif kind == "code":
            add_code_block(payload)
        elif kind == "image":
            add_picture(payload[0], payload[1])
        elif kind == "pagebreak":
            doc.add_page_break()
        elif kind == "hr":
            pass

    doc.save(out_docx)


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

_MD_DIR = "."


def main(argv=None):
    global _MD_DIR
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("lang", choices=("fa", "en"))
    ap.add_argument("source", help="Markdown report source")
    ap.add_argument("out_stem", help="output path without extension (dir/REPORT_EN)")
    ap.add_argument("--toc-json", default=None, help="sidecar path for DOCX static TOC (default: out_stem.toc.json)")
    a = ap.parse_args(argv)

    src = Path(a.source).resolve()
    _MD_DIR = str(src.parent)
    text = src.read_text(encoding="utf-8")
    meta, body = parse_front_matter(text)
    appendix_name = meta.get("appendix", "").strip()
    if appendix_name:
        appendix_path = (src.parent / appendix_name).resolve()
        if not appendix_path.is_file():
            raise FileNotFoundError(f"configured report appendix does not exist: {appendix_path}")
        body += "\n\n" + appendix_path.read_text(encoding="utf-8")
    blocks = parse_blocks(body)

    out_stem = Path(a.out_stem).resolve()
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    pdf_path = str(out_stem) + ".pdf"
    docx_path = str(out_stem) + ".docx"
    toc_json = Path(a.toc_json) if a.toc_json else Path(str(out_stem) + ".toc.json")

    n_toc = len([b for b in blocks if b[0] in ("h1", "h2")])
    frame_h = A4[1] - 52 - 48
    lead = 13.6 if a.lang == "fa" else 13.0
    lines_per = int((frame_h - 70 - 8) // lead)
    n_toc_pages = max(1, -(-n_toc // lines_per))

    # first build: placeholder TOC pages (identical frame heights) that also
    # records which page every heading lands on
    doc = build_pdf(a.lang, blocks, meta, pdf_path, toc_entries=None, n_toc_pages=n_toc_pages)
    all_headings = list(doc.heading_pages)
    toc_entries = [(l, t, p) for (l, t, p) in all_headings if l in (1, 2)]
    # final build: same pagination, TOC pages filled with the measured numbers
    build_pdf(a.lang, blocks, meta, pdf_path, toc_entries=toc_entries, n_toc_pages=n_toc_pages)
    toc_json.write_text(json.dumps(toc_entries, ensure_ascii=False), encoding="utf-8")

    build_docx(a.lang, blocks, meta, docx_path, toc_entries, src.parent)

    from pypdf import PdfReader
    pages = len(PdfReader(pdf_path).pages)
    print(f"BUILT {pdf_path} ({pages} pages)")
    print(f"BUILT {docx_path}")
    minimum_pages = int(os.environ.get("REPORT_MIN_PAGES", "41"))
    if pages < minimum_pages:
        raise SystemExit(f"FAIL: {pdf_path} has {pages} pages; minimum is {minimum_pages}")
    print(f"OK: page count verified >= {minimum_pages}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
