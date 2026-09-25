#!/usr/bin/env python3
"""Crop visual stimuli for exam 2 without performing OCR."""

from pathlib import Path
from PIL import Image

from crop_ayin1_exam1 import remove_green_answer_marks, trim_white

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("/private/tmp/ayeenname-ayin1-hi")
OUTPUT = ROOT / "assets" / "questions"

CROPS = {
    1: (5, 495, 345, 935, 735),
    2: (5, 55, 345, 470, 735),
    3: (5, 510, 720, 750, 960),
    4: (5, 55, 700, 255, 930),
    5: (5, 500, 1060, 700, 1310),
    6: (5, 50, 1060, 240, 1320),
    7: (6, 525, 45, 905, 230),
    8: (6, 45, 55, 255, 255),
    12: (6, 45, 730, 285, 980),
    19: (6, 1550, 715, 1815, 915),
    23: (5, 1570, 100, 1880, 285),
    24: (5, 1050, 105, 1410, 285),
    28: (5, 1010, 760, 1230, 1015),
    29: (5, 1540, 1040, 1715, 1330),
    30: (5, 1040, 1110, 1320, 1435),
}

NO_GREEN_MASK = {12, 19, 30}
MANUAL_PATCHES = {
    1: (390, 225, 440, 325),
    2: (355, 235, 415, 335),
}

OUTPUT.mkdir(parents=True, exist_ok=True)
for number, (page, left, top, right, bottom) in CROPS.items():
    image = Image.open(SOURCE / f"page-{page:02}.png").convert("RGB")
    crop = image.crop((left, top, right, bottom))
    if number not in NO_GREEN_MASK:
        crop = remove_green_answer_marks(crop)
    if number in MANUAL_PATCHES:
        x0, y0, x1, y1 = MANUAL_PATCHES[number]
        crop.paste((219, 219, 160), (x0, y0, x1, y1))
    crop = trim_white(crop)
    crop.save(OUTPUT / f"q-src-ayin1-e02-p{page:02}-n{number:02}.png", optimize=True)

print(f"saved {len(CROPS)} crops")
