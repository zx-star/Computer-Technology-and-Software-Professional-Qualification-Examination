#!/usr/bin/env python3
"""Extract the supplied textbook PDF into searchable VitePress Markdown pages."""

from __future__ import annotations

import re
import subprocess
import html
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


PDF = Path("/Users/zhouxin/Downloads/教材原文.pdf")
OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "textbook"

# PDF page numbers are 1-based. The first 14 pages contain the cover, preface,
# contents, and publishing information; chapter 1 starts on PDF page 15.
CHAPTERS = [
    (1, 15, "绪论"),
    (2, 36, "计算机系统基础知识"),
    (3, 117, "信息系统基础知识"),
    (4, 157, "信息安全技术基础知识"),
    (5, 187, "软件工程基础知识"),
    (6, 230, "数据库设计基础知识"),
    (7, 260, "系统架构设计基础知识"),
    (8, 283, "系统质量属性与架构评估"),
    (9, 317, "软件可靠性基础知识"),
    (10, 342, "软件架构的演化和维护"),
    (11, 381, "未来信息综合技术"),
    (12, 417, "信息系统架构设计理论与实践"),
    (13, 463, "层次式架构设计理论与实践"),
    (14, 494, "云原生架构设计理论与实践"),
    (15, 524, "面向服务架构设计理论与实践"),
    (16, 553, "嵌入式系统架构设计理论与实践"),
    (17, 611, "通信系统架构设计理论与实践"),
    (18, 645, "安全架构设计理论与实践"),
    (19, 688, "大数据架构设计理论与实践"),
    (20, 714, "系统架构设计师论文写作要点"),
]

# The PDF text layer stores Latin letters and digits as full-width forms such
# as ``Ｃｅｎｔｒａｌ`` (U+FF21..U+FF5E). Browsers render them at CJK glyph
# width, which reads like excessive letter spacing, so map them to ASCII.
FULLWIDTH_ASCII = str.maketrans(
    "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"
    "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
    "０１２３４５６７８９",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789",
)


@dataclass
class TextRun:
    text: str
    color: str
    left: int


@dataclass
class VisualLine:
    top: int
    left: int
    runs: list[TextRun]


def extract_pages(start: int, end: int) -> list[list[VisualLine]]:
    result = subprocess.run(
        [
            "pdftohtml",
            "-f",
            str(start),
            "-l",
            str(end),
            "-xml",
            "-i",
            "-stdout",
            str(PDF),
        ],
        check=True,
        capture_output=True,
    )
    root = ET.fromstring(result.stdout)
    pages = []
    for page in root.findall("page"):
        fonts = {
            node.attrib["id"]: node.attrib.get("color", "#000000").lower()
            for node in page.findall("fontspec")
        }
        by_top: dict[int, list[TextRun]] = {}
        for node in page.findall("text"):
            text = "".join(node.itertext())
            if not text.strip():
                continue
            top = int(node.attrib.get("top", "0"))
            left = int(node.attrib.get("left", "0"))
            by_top.setdefault(top, []).append(
                TextRun(text, fonts.get(node.attrib.get("font", ""), "#000000"), left)
            )
        pages.append(
            [
                VisualLine(top, min(run.left for run in runs), sorted(runs, key=lambda run: run.left))
                for top, runs in sorted(by_top.items())
            ]
        )
    return pages


def normalize_text(text: str) -> str:
    text = text.translate(FULLWIDTH_ASCII)
    text = normalize_acronym_spacing(re.sub(r"\s+", " ", text).strip())
    # Chinese prose normally has no inter-character spaces. Some headings and
    # labels in the PDF store each glyph separately, producing ``关 系 运 算``.
    cjk = r"\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
    text = re.sub(rf"(?<=[{cjk}])\s+(?=[{cjk}])", "", text)
    return text


def normalize_acronym_spacing(text: str) -> str:
    """Remove layout spaces inside full-width Latin acronyms.

    The PDF stores some letterforms as separate positioned glyphs, producing
    strings such as ``Ｘ Ｍ Ｌ`` and ``Ｎ ｏ Ｓ Ｑ Ｌ``. Normal English phrases
    such as ``System Architecture`` are intentionally left unchanged.
    """

    latin = r"A-Za-zＡ-Ｚａ-ｚ"

    # Join runs made from individually positioned glyphs: ``Ｘ Ｍ Ｌ`` and
    # ``Ｎ ｏ Ｓ Ｑ Ｌ``. A sequence must contain at least two tokens so that
    # normal prose such as ``System Architecture`` is not affected.
    single_letter_run = re.compile(
        rf"(?<![{latin}])(?:[{latin}]\s+)+[{latin}](?![{latin}])"
    )
    text = single_letter_run.sub(lambda match: re.sub(r"\s+", "", match.group(0)), text)

    # ``No SQL`` is the one multi-letter phrase in this book that is commonly
    # printed as the single product/concept name ``NoSQL``.
    text = re.sub(r"Ｎｏ\s+ＳＱＬ", "ＮｏＳＱＬ", text)
    text = re.sub(r"Ｎｏｔ\s+Ｏｎｌｙ", "Ｎｏｔ Ｏｎｌｙ", text)
    return text


def render_run(run: TextRun) -> str:
    text = html.escape(normalize_text(run.text), quote=False)
    if not text or run.color in {"#000000", "#000", "black"}:
        return text
    return f'<span style="color: {run.color}">{text}</span>'


def render_line(line: VisualLine) -> str:
    rendered = []
    previous_plain = ""
    for run in line.runs:
        plain = normalize_text(run.text)
        if previous_plain and plain:
            gap_match = re.match(r"^\s+", plain)
            if gap_match and normalize_acronym_spacing(previous_plain + plain) != previous_plain + plain:
                plain = plain[gap_match.end():]
        value = render_run(TextRun(plain, run.color, run.left))
        if value:
            rendered.append(value)
            previous_plain = (previous_plain + plain)[-32:]
    return "".join(rendered)


def join_wrapped_lines(lines: list[VisualLine]) -> str:
    """Join PDF visual lines without inserting spaces into Chinese text."""
    rendered = ""
    previous_text = ""
    for line in lines:
        text = "".join(normalize_text(run.text) for run in line.runs)
        if rendered and previous_text and previous_text[-1].isascii() and previous_text[-1].isalnum() \
                and text and text[0].isascii() and text[0].isalnum():
            rendered += " "
        rendered += render_line(line)
        previous_text = text
    return rendered


def clean_page(page: list[VisualLine], chapter_title: str | None = None) -> list[str]:
    # Repeated running headers and printed page numbers add noise to web pages.
    header_pattern = re.compile(r"^第\s*[０-９0-9]+\s*章.*$")
    cleaned: list[VisualLine] = []
    for line in page:
        plain = normalize_text("".join(run.text for run in line.runs))
        compact = plain.replace(" ", "")
        if "系统架构设计师教程" in compact:
            continue
        if re.fullmatch(r"[０-９0-9]+", compact):
            continue
        if chapter_title and header_pattern.match(plain):
            continue
        cleaned.append(line)

    # Blank lines in the PDF text layer are useful paragraph boundaries. Keep
    # headings and numbered/bulleted items as their own Markdown blocks.
    paragraphs: list[str] = []
    current: list[str] = []
    item_pattern = re.compile(
        r"^(?:[●•]|[（(][０-９0-9一二三四五六七八九十]+[）)]|[０-９0-9]+[．.）)])"
    )
    heading_pattern = re.compile(r"^[０-９0-9]+(?:[．.][０-９0-9]+){0,2}\s*[^。！？：；]{1,32}$")
    previous_top = None
    for line in cleaned + [None]:
        plain = normalize_text("".join(run.text for run in line.runs)) if line else ""
        has_paragraph_gap = previous_top is not None and line is not None and line.top - previous_top > 30
        if line is None or has_paragraph_gap:
            if current:
                paragraphs.append(join_wrapped_lines(current))
                current = []
            if line is None:
                continue
        if heading_pattern.match(plain):
            if current:
                paragraphs.append(join_wrapped_lines(current))
                current = []
            paragraphs.append(f"## {render_line(line)}")
            previous_top = line.top
            continue
        if current and item_pattern.match(plain):
            paragraphs.append(join_wrapped_lines(current))
            current = []
        current.append(line)
        previous_top = line.top

    return paragraphs


def page_blocks(start: int, end: int, title: str | None = None) -> list[str]:
    pages = extract_pages(start, end)
    blocks = []
    for offset, page in enumerate(pages):
        paragraphs = clean_page(page, title)
        if paragraphs:
            blocks.append(
                f"<!-- PDF 第 {start + offset} 页 -->\n\n" + "\n\n".join(paragraphs)
            )
    return blocks


def write_page(path: Path, heading: str, blocks: list[str], note: str = "") -> None:
    content = [f"# {heading}", "", note, "" if note else None]
    content = [part for part in content if part is not None]
    content.extend(blocks)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n\n".join(content).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    if not PDF.exists():
        raise SystemExit(f"PDF not found: {PDF}")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    starts = [start for _, start, _ in CHAPTERS]
    total_pages = 725

    write_page(
        OUTPUT / "index.md",
        "教材原文",
        page_blocks(1, starts[0] - 1),
        "> 根据《教材原文.pdf》提取的可搜索文字内容。图片暂未提取；页眉、页码和分页符已做网页阅读优化。",
    )

    for index, (number, start, title) in enumerate(CHAPTERS):
        end = starts[index + 1] - 1 if index + 1 < len(starts) else total_pages
        write_page(
            OUTPUT / f"chapter-{number:02d}" / "index.md",
            f"第{number}章 {title}",
            page_blocks(start, end, title),
            "> 本页为教材原文文字提取版。教材中的图片暂未提取。",
        )

    print(f"Generated {len(CHAPTERS) + 1} pages in {OUTPUT}")


if __name__ == "__main__":
    main()
