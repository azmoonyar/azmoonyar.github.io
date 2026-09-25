#!/usr/bin/env python3
"""Crop visual stimuli for exam 10. No OCR is performed."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("/private/tmp/ayeenname-ayin1-exam10")
OUTPUT = ROOT / "assets" / "questions"

CROPS = {
    2: (29, 85, 455, 305, 670),
    3: (29, 685, 935, 900, 1145),
    4: (29, 75, 925, 315, 1085),
    5: (29, 690, 1360, 875, 1525),
    6: (29, 65, 1360, 310, 1590),
    7: (30, 1960, 125, 2205, 340),
    8: (30, 1420, 140, 1515, 335),
    23: (29, 1940, 145, 2245, 415),
    25: (29, 1930, 560, 2215, 815),
    29: (29, 1980, 1350, 2195, 1590),
    30: (29, 1370, 1370, 1690, 1610),
}

COMPOSITES = {
    1: (29, [(1000, 500, 1175, 690), (730, 500, 855, 690), (1000, 690, 1175, 895), (730, 690, 910, 895)]),
    24: (29, [(1635, 155, 1785, 330), (1385, 155, 1535, 330), (1635, 345, 1785, 505), (1385, 345, 1515, 505)]),
}


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
for number, (page, boxes) in COMPOSITES.items():
    source = Image.open(SOURCE / f"page-{page}.png").convert("RGB")
    composite(source, boxes).save(OUTPUT / f"q-src-ayin1-e10-p{page}-n{number:02}.png", optimize=True)
for number, (page, left, top, right, bottom) in CROPS.items():
    source = Image.open(SOURCE / f"page-{page}.png").convert("RGB")
    source.crop((left, top, right, bottom)).save(
        OUTPUT / f"q-src-ayin1-e10-p{page}-n{number:02}.png", optimize=True
    )
print(f"saved {len(CROPS) + len(COMPOSITES)} crops")
