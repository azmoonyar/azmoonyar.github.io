#!/usr/bin/env python3
"""Re-crop question pictures whose original crop missed the stimulus.

Each of these files showed option text, another question's text, half a sign or an
answer asterisk instead of the question's own picture. Boxes were measured visually
with a coordinate ruler on page renders of the source PDFs; file names are unchanged
(one missing picture, 4_5888 page 4 question 16, gets a new file referenced through
data/question-corrections.js). No OCR is involved.

usage: fix_broken_question_images.py
"""
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "assets" / "questions"
RENDERS = ROOT / "tmp" / "pdfs" / "fix-renders"

SOURCES = {
    # key: (pdf file, render path pattern, long edge in px)
    "600": ("600-driveing.pdf", RENDERS / "600-p{page:03d}.png", 1800),
    "tablo": ("tablo.pdf", RENDERS / "tablo-p{page:03d}.png", 1600),
    "first": ("4_5888983329180487891-1.pdf", ROOT / "tmp" / "pdfs" / "first-pdf-pages-4-10" / "page-{page:02d}.png", 2105),
}

CROPS = {
    "q-src-600-driveing-p044-n23.png": ("600", 44, (690, 1565, 848, 1722)),    # parking on a downhill with curb (was option text)
    "q-src-600-driveing-p065-n26.png": ("600", 65, (70, 160, 305, 455)),       # zone sign without the answer asterisk
    "q-src-600-driveing-p081-n27.png": ("600", 81, (690, 724, 975, 986)),      # end-of-all-restrictions sign (was half a sign + text)
    "q-src-600-driveing-p083-n14.png": ("600", 83, (80, 938, 270, 1114)),      # two-car crossroads figure (was another question's text)
    "q-src-600-driveing-p079-n11.png": ("600", 79, (682, 703, 964, 954)),      # traffic photo (was pedal text + half the photo + answer text)
    "q-src-tablo-p110-n278.png": ("tablo", 111, (0, 20, 372, 372)),            # 30 km/h sign printed at the top of the next page
    "q-src-4-5888983329180487891-1-p008-n07.png": ("first", 8, (783, 966, 864, 1098)),   # green light + red arrow (was option text)
    "q-src-4-5888983329180487891-1-p004-n16.png": ("first", 4, (113, 1736, 412, 1850)),  # parking figure (question had no picture)
}


def page_image(source, page):
    pdf, pattern, long_edge = SOURCES[source]
    path = Path(str(pattern).format(page=page))
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["swift", str(ROOT / "scripts" / "render_pdf_pages.swift"), str(ROOT / "pdf's" / pdf), str(page), str(page), str(path.parent), str(long_edge)], check=True)
        rendered = path.parent / f"page-{page:03d}.png"
        if rendered != path:
            rendered.rename(path)
    return Image.open(path).convert("RGB")


def main():
    for name, (source, page, box) in CROPS.items():
        page_image(source, page).crop(box).save(OUTPUT / name, optimize=True)
    print(f"re-cropped {len(CROPS)} question pictures")


if __name__ == "__main__":
    main()
