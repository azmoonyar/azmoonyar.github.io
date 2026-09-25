#!/usr/bin/env python3
"""Crop visual stimuli for exam 5. No OCR is performed."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("/private/tmp/ayeenname-ayin1-next")
OUTPUT = ROOT / "assets" / "questions"

CROPS = {
    3: (14, 750, 850, 895, 1060),
    4: (14, 85, 850, 285, 1060),
    5: (14, 750, 1260, 940, 1475),
    6: (14, 75, 1250, 290, 1515),
    7: (15, 1940, 145, 2110, 380),
    8: (15, 1390, 180, 1550, 380),
    23: (14, 1930, 115, 2260, 335),
    24: (14, 1380, 125, 1705, 370),
    29: (14, 1950, 1360, 2225, 1685),
}

COMPOSITES = {
    1: (14, [(1010, 485, 1160, 640), (745, 485, 900, 640), (1010, 675, 1160, 840), (745, 675, 835, 840)]),
    2: (14, [(395, 490, 565, 640), (145, 490, 280, 640), (395, 675, 565, 835), (145, 675, 315, 835)]),
    27: (14, [(2180, 940, 2340, 1125), (1930, 940, 2075, 1125), (2180, 1140, 2340, 1320), (1930, 1140, 2050, 1320)]),
    28: (14, [(1670, 940, 1820, 1125), (1415, 940, 1510, 1125), (1670, 1140, 1820, 1320), (1415, 1140, 1560, 1320)]),
}


def composite(source: Image.Image, boxes: list[tuple[int, int, int, int]]) -> Image.Image:
    canvas = Image.new("RGB", (500, 390), "white")
    font_path = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
    font = ImageFont.truetype(str(font_path), 28) if font_path.exists() else ImageFont.load_default()
    positions = [(275, 15), (15, 15), (275, 205), (15, 205)]
    draw = ImageDraw.Draw(canvas)
    for number, (box, (x, y)) in enumerate(zip(boxes, positions), start=1):
        option = source.crop(box)
        option.thumbnail((175, 160))
        canvas.paste(option, (x + (175 - option.width) // 2, y + 18 + (160 - option.height) // 2))
        draw.text((x + 195, y + 78), str(number), fill="black", font=font)
    return canvas


OUTPUT.mkdir(parents=True, exist_ok=True)
for number, (page, box) in COMPOSITES.items():
    image = Image.open(SOURCE / f"page-{page}.png").convert("RGB")
    composite(image, box).save(OUTPUT / f"q-src-ayin1-e05-p{page:02}-n{number:02}.png", optimize=True)

for number, (page, left, top, right, bottom) in CROPS.items():
    image = Image.open(SOURCE / f"page-{page}.png").convert("RGB")
    image.crop((left, top, right, bottom)).save(OUTPUT / f"q-src-ayin1-e05-p{page:02}-n{number:02}.png", optimize=True)

print(f"saved {len(CROPS) + len(COMPOSITES)} crops")
