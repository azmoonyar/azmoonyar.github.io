#!/usr/bin/env python3
"""Crop visual stimuli for exam 7. No OCR is performed."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("/private/tmp/ayeenname-ayin1-exam7")
OUTPUT = ROOT / "assets" / "questions"

CROPS = {
    2: (20, 80, 500, 290, 710),
    3: (20, 650, 940, 900, 1150),
    4: (20, 75, 900, 285, 1110),
    5: (20, 650, 1370, 900, 1585),
    6: (20, 75, 1350, 300, 1590),
    7: (21, 1940, 130, 2110, 310),
    8: (21, 1380, 180, 1585, 390),
    18: (21, 70, 540, 280, 760),
    22: (21, 75, 1370, 365, 1535),
    23: (20, 1940, 150, 2160, 360),
    26: (20, 1380, 690, 1635, 870),
    28: (20, 1380, 900, 1570, 1145),
    29: (20, 1950, 1375, 2120, 1590),
}

OPTION_BOXES = [
    (1010, 610, 1170, 765),
    (750, 610, 825, 765),
    (1010, 755, 1170, 900),
    (750, 755, 900, 900),
]


def option_composite(source: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", (500, 390), "white")
    font_path = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
    font = ImageFont.truetype(str(font_path), 28) if font_path.exists() else ImageFont.load_default()
    positions = [(275, 15), (15, 15), (275, 205), (15, 205)]
    draw = ImageDraw.Draw(canvas)
    for number, (box, (x, y)) in enumerate(zip(OPTION_BOXES, positions), start=1):
        option = source.crop(box)
        option.thumbnail((175, 160))
        canvas.paste(option, (x + (175 - option.width) // 2, y + 18 + (160 - option.height) // 2))
        draw.text((x + 195, y + 78), str(number), fill="black", font=font)
    return canvas


OUTPUT.mkdir(parents=True, exist_ok=True)
page20 = Image.open(SOURCE / "page-20.png").convert("RGB")
option_composite(page20).save(OUTPUT / "q-src-ayin1-e07-p20-n01.png", optimize=True)

for number, (page, left, top, right, bottom) in CROPS.items():
    image = Image.open(SOURCE / f"page-{page}.png").convert("RGB")
    image.crop((left, top, right, bottom)).save(
        OUTPUT / f"q-src-ayin1-e07-p{page:02}-n{number:02}.png",
        optimize=True,
    )

print(f"saved {len(CROPS) + 1} crops")
