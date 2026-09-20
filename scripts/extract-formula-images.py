#!/usr/bin/env python3
"""Render the database-join formulas that the PDF text layer cannot decode."""

from pathlib import Path
import subprocess

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PDF = Path("/Users/zhouxin/Downloads/教材原文.pdf")
OUTPUT = ROOT / "docs/textbook/chapter-06/images"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rendered = Path("/tmp/ruankao-formula-page-241.png")
    subprocess.run(
        [
            "pdftoppm", "-f", "241", "-l", "241", "-r", "150", "-png",
            "-singlefile", str(PDF), str(rendered.with_suffix("")),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    with Image.open(rendered) as page:
        # Coordinates are in the 150-DPI render. Keep enough surrounding
        # whitespace for the formulas to remain legible in the document.
        crops = {
            "formula-theta-definition.png": (145, 330, 930, 390),
            "formula-theta-columns.png": (180, 515, 920, 570),
            "formula-theta-selection.png": (180, 650, 930, 715),
            "formula-equi-join.png": (160, 760, 925, 825),
            "formula-natural-join-definition.png": (130, 1025, 955, 1090),
            "formula-natural-join-selection.png": (100, 1115, 975, 1195),
        }
        for name, box in crops.items():
            page.crop(box).save(OUTPUT / name, "PNG", optimize=True)


if __name__ == "__main__":
    main()
