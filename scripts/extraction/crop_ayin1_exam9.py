#!/usr/bin/env python3
"""Crop visual stimuli for exam 9. No OCR is performed."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("/private/tmp/ayeenname-ayin1-exam9")
OUTPUT = ROOT / "assets" / "questions"

CROPS = {
    2: (26, 115, 490, 325, 675),
    3: (26, 730, 945, 910, 1115),
    4: (26, 95, 930, 325, 1140),
    5: (26, 720, 1370, 885, 1580),
    6: (26, 105, 1385, 330, 1600),
    7: (27, 1990, 140, 2215, 345),
    8: (27, 1500, 175, 1855, 385),
    16: (27, 155, 165, 485, 515),
    19: (27, 690, 1005, 910, 1260),
    21: (27, 670, 1350, 900, 1595),
    23: (26, 1960, 135, 2245, 375),
    24: (26, 1320, 105, 1535, 350),
    25: (26, 1900, 565, 2245, 825),
    28: (26, 1380, 950, 1650, 1115),
}

Q1_OPTIONS = [
    (1000, 515, 1175, 700),
    (730, 515, 920, 700),
    (1000, 700, 1175, 895),
    (725, 700, 855, 895),
]


def composite(source, boxes):
    canvas = Image.new("RGB", (500, 390), "white")
    draw = ImageDraw.Draw(canvas)
    font_path = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
    font = ImageFont.truetype(str(font_path), 28) if font_path.exists() else ImageFont.load_default()
    positions = [(275, 15), (15, 15), (275, 205), (15, 205)]
    for number, (box, (x, y)) in enumerate(zip(boxes, positions), 1):
        item = source.crop(box)
        item.thumbnail((175, 160))
        canvas.paste(item, (x + (175 - item.width) // 2, y + 18 + (160 - item.height) // 2))
        draw.text((x + 195, y + 78), str(number), fill="black", font=font)
    return canvas


OUTPUT.mkdir(parents=True, exist_ok=True)
page26 = Image.open(SOURCE / "page-26.png").convert("RGB")
composite(page26, Q1_OPTIONS).save(OUTPUT / "q-src-ayin1-e09-p26-n01.png", optimize=True)
for number, (page, left, top, right, bottom) in CROPS.items():
    source = Image.open(SOURCE / f"page-{page}.png").convert("RGB")
    source.crop((left, top, right, bottom)).save(
        OUTPUT / f"q-src-ayin1-e09-p{page}-n{number:02}.png", optimize=True
    )
print(f"saved {len(CROPS) + 1} crops")
