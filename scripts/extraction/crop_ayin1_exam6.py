#!/usr/bin/env python3
"""Crop visual stimuli for exam 6. No OCR is performed."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("/private/tmp/ayeenname-ayin1-exam6")
OUTPUT = ROOT / "assets" / "questions"

CROPS = {
    2: (17, 85, 520, 290, 730),
    3: (17, 755, 930, 925, 1140),
    4: (17, 80, 930, 275, 1140),
    5: (17, 760, 1390, 930, 1610),
    6: (17, 80, 1380, 285, 1620),
    7: (18, 1950, 120, 2130, 330),
    8: (18, 1380, 180, 1585, 360),
    24: (17, 1380, 170, 1710, 405),
    27: (17, 1940, 920, 2185, 1220),
    28: (17, 1380, 925, 1560, 1140),
    29: (17, 1960, 1390, 2100, 1535),
    30: (17, 1380, 1350, 1510, 1645),
}

OPTION_BOXES = [
    (1010, 560, 1170, 715),
    (750, 560, 875, 715),
    (1010, 720, 1170, 880),
    (750, 720, 900, 880),
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
page17 = Image.open(SOURCE / "page-17.png").convert("RGB")
option_composite(page17).save(OUTPUT / "q-src-ayin1-e06-p17-n01.png", optimize=True)

for number, (page, left, top, right, bottom) in CROPS.items():
    image = Image.open(SOURCE / f"page-{page}.png").convert("RGB")
    image.crop((left, top, right, bottom)).save(
        OUTPUT / f"q-src-ayin1-e06-p{page:02}-n{number:02}.png",
        optimize=True,
    )

print(f"saved {len(CROPS) + 1} crops")
