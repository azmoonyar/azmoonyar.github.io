#!/usr/bin/env python3
"""Crop the visual stimuli for exam 4 without performing OCR."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from crop_ayin1_exam1 import trim_white


ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("/private/tmp/ayeenname-ayin1-hi")
OUTPUT = ROOT / "assets" / "questions"

# question: (rendered PDF page, left, top, right, bottom)
CROPS = {
    1: (11, 520, 410, 930, 700),
    2: (11, 55, 410, 445, 690),
    3: (11, 525, 735, 660, 865),
    4: (11, 70, 705, 205, 855),
    5: (11, 525, 1080, 670, 1225),
    6: (11, 65, 1090, 185, 1240),
    7: (12, 1575, 125, 1685, 310),
    8: (12, 1110, 125, 1440, 215),
    14: (12, 1110, 1130, 1355, 1435),
    24: (11, 1055, 100, 1320, 285),
    27: (11, 1545, 705, 1690, 845),
    28: (11, 1045, 700, 1190, 855),
    29: (11, 1570, 1080, 1995, 1430),
    30: (11, 1035, 1135, 1145, 1360),
}

# Source answer stamps that overlap a multi-choice visual are removed with one
# small, fixed patch. This avoids interpreting the green artwork in signs/diagrams
# as an answer stamp and keeps every actual visual intact.
COMPOSITES = {
    1: [
        (755, 420, 875, 545),
        (535, 420, 660, 545),
        (750, 565, 875, 695),
        (535, 565, 650, 695),
    ],
    2: [
        (285, 415, 410, 545),
        (65, 420, 220, 545),
        (285, 560, 420, 680),
        (65, 550, 225, 690),
    ],
    29: [
        (1810, 1125, 1905, 1225),
        (1585, 1120, 1705, 1230),
        (1810, 1270, 1915, 1390),
        (1580, 1265, 1705, 1390),
    ],
}


def make_option_composite(source: Image.Image, boxes: list[tuple[int, int, int, int]]) -> Image.Image:
    """Build a clean 2x2 stimulus grid while preserving the source option order."""
    canvas = Image.new("RGB", (460, 360), "white")
    font_path = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
    font = ImageFont.truetype(str(font_path), 27) if font_path.exists() else ImageFont.load_default()
    positions = [(250, 20), (20, 20), (250, 190), (20, 190)]
    for index, (box, (x, y)) in enumerate(zip(boxes, positions), start=1):
        option = source.crop(box)
        option.thumbnail((155, 135))
        canvas.paste(option, (x + (155 - option.width) // 2, y + 25 + (135 - option.height) // 2))
        ImageDraw.Draw(canvas).text((x + 172, y + 76), str(index), fill="black", font=font)
    return canvas

OUTPUT.mkdir(parents=True, exist_ok=True)
for number, (page, left, top, right, bottom) in CROPS.items():
    page_image = Image.open(SOURCE / f"page-{page:02}.png").convert("RGB")
    crop = make_option_composite(page_image, COMPOSITES[number]) if number in COMPOSITES else page_image.crop((left, top, right, bottom))
    crop = trim_white(crop)
    crop.save(OUTPUT / f"q-src-ayin1-e04-p{page:02}-n{number:02}.png", optimize=True)

print(f"saved {len(CROPS)} crops")
