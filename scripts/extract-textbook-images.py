#!/usr/bin/env python3
"""Extract textbook figures from the scanned PDF and insert them before captions."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


PDF = Path("/Users/zhouxin/Downloads/教材原文.pdf")
ROOT = Path(__file__).resolve().parents[1]
TEXTBOOK = ROOT / "docs" / "textbook"

CHAPTERS = [
    (1, 15), (2, 36), (3, 117), (4, 157), (5, 187), (6, 230),
    (7, 260), (8, 283), (9, 317), (10, 342), (11, 381), (12, 417),
    (13, 463), (14, 494), (15, 524), (16, 553), (17, 611), (18, 645),
    (19, 688), (20, 714),
]


@dataclass
class Caption:
    number: str
    text: str
    top: int
    left: int
    width: int
    height: int


def chapter_for_page(page: int) -> int | None:
    current = None
    for number, start in CHAPTERS:
        if start <= page:
            current = number
        else:
            break
    return current


def normalize(value: str) -> str:
    return re.sub(r"\s+", "", value).replace("·", "")


def figure_number(text: str) -> str | None:
    match = re.search(r"图\s*([０-９0-9]+)\s*[－−-]\s*([０-９0-9]+)", text)
    if not match:
        return None
    return f"{match.group(1)}-{match.group(2)}"


def read_captions() -> dict[int, list[Caption]]:
    result = subprocess.run(
        ["pdftohtml", "-xml", "-i", "-stdout", str(PDF)],
        check=True,
        capture_output=True,
    )
    root = ET.fromstring(result.stdout)
    pages: dict[int, list[Caption]] = {}
    for page_node in root.findall("page"):
        page_number = int(page_node.attrib["number"])
        captions = []
        for node in page_node.findall("text"):
            text = "".join(node.itertext()).strip()
            number = figure_number(text)
            if not number or "如图" in text or "所示" in text:
                continue
            # Captions are short labels. This excludes ordinary paragraphs that
            # merely reference a figure while retaining long figure titles.
            if len(text) > 80:
                continue
            captions.append(
                Caption(
                    number,
                    text,
                    int(node.attrib.get("top", 0)),
                    int(node.attrib.get("left", 0)),
                    int(node.attrib.get("width", 0)),
                    int(node.attrib.get("height", 0)),
                )
            )
        pages[page_number] = captions
    return pages


def render_page(page: int, output: Path) -> None:
    subprocess.run(
        [
            "pdftoppm", "-f", str(page), "-l", str(page), "-r", "120",
            "-jpeg", "-jpegopt", "quality=90", "-singlefile", str(PDF), str(output.with_suffix("")),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def insert_image(text: str, caption: Caption, image_ref: str) -> str:
    # Captions are emitted as their own Markdown paragraph by the text
    # extractor. References such as ``如图 1-1 所示`` must remain in prose.
    pattern = re.compile(
        rf"(?m)^(?!\s*(?:如图|见图))\s*(图\s*{re.escape(caption.number.split('-')[0])}"
        rf"\s*[－−-]\s*{re.escape(caption.number.split('-')[1])}[^\n]*)"
    )
    matches = [match for match in pattern.finditer(text) if not re.search(r"给出|所示|见图|）。", match.group(1))]
    if not matches:
        return text
    match = matches[0]
    marker = f"![{caption.text}]({image_ref})\n\n"
    return text[: match.start()] + marker + text[match.start() :]


def process_page(page: int, captions: list[Caption], page_text: str, temp_dir: Path) -> str:
    chapter = chapter_for_page(page)
    if chapter is None or not captions:
        return page_text
    page_image = temp_dir / f"page-{page}.jpg"
    render_page(page, page_image)
    with Image.open(page_image) as source:
        scale_x = source.width / 774
        scale_y = source.height / 987
        for caption in captions:
            image_dir = TEXTBOOK / f"chapter-{chapter:02d}" / "images"
            image_dir.mkdir(parents=True, exist_ok=True)
            image_name = f"figure-{caption.number}.png"
            image_path = image_dir / image_name
            top = max(0, caption.top - 420)
            bottom = min(987, caption.top + caption.height + 12)
            # Figure captions are usually centered, so their x-position is
            # not the figure's left edge. Use the book's full text column;
            # otherwise centered diagrams lose their left half.
            left = 45
            right = 730
            crop = source.crop((int(left * scale_x), int(top * scale_y), int(right * scale_x), int(bottom * scale_y)))
            crop.save(image_path, "PNG", optimize=True)
            page_text = insert_image(page_text, caption, f"./images/{image_name}")
    return page_text


def main() -> None:
    if not PDF.exists():
        raise SystemExit(f"PDF not found: {PDF}")
    captions_by_page = read_captions()
    with tempfile.TemporaryDirectory(prefix="ruankao-textbook-images-") as temp:
        temp_dir = Path(temp)
        for path in sorted(TEXTBOOK.glob("chapter-*/index.md")):
            content = re.sub(r"!\[[^\]]*\]\([^)]*/images/figure-[^)]*\)\n*", "", path.read_text(encoding="utf-8"))
            page_pattern = re.compile(r"(<!-- PDF 第 (\d+) 页 -->)(.*?)(?=<!-- PDF 第 \d+ 页 -->|\Z)", re.S)
            changed = content
            for match in list(page_pattern.finditer(content)):
                page = int(match.group(2))
                block = match.group(0)
                updated = process_page(page, captions_by_page.get(page, []), block, temp_dir)
                changed = changed.replace(block, updated, 1)
            path.write_text(changed, encoding="utf-8")
    # Remove the old note now that figures are present.
    for path in TEXTBOOK.glob("chapter-*/index.md"):
        value = path.read_text(encoding="utf-8")
        value = value.replace("教材中的图片暂未提取。", "图示已按 PDF 页面裁剪并插入正文图注前。")
        path.write_text(value, encoding="utf-8")
    print("Inserted textbook figures")


if __name__ == "__main__":
    main()
