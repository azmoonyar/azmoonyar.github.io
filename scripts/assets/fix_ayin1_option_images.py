#!/usr/bin/env python3
"""Rebuild ایین نامه-1.pdf question pictures from the source pages without answer marks.

1. Option-order fixes: three questions (exam 12 q1, exam 13 q1, exam 13 q24) were cloned from
   600-driveing.pdf with an ayin1 answer override but kept the 600-driveing picture, whose option
   order differs, so the picture contradicted the key; q-600-e7-p033-n30 is the reverse case
   (merged with exam 6 q1). Their pictures are rebuilt from the ayin1 pages (see
   data/question-corrections.js).
2. Answer-mark fixes: several ayin1 crops still contained the green check printed next to the
   correct option (or the option text around it). They are rebuilt from the page render with
   tight boxes that exclude the check; where the check touches a sign, the touched pixels are
   restored from the sign's mirror side or the surrounding paper.

Boxes were measured visually on 3000 px renders with a coordinate ruler. File names are
unchanged. No OCR is involved.

usage: fix_ayin1_option_images.py
"""
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "pdf's" / "ایین نامه-1.pdf"
RENDERS = ROOT / "tmp" / "pdfs" / "ayin1-3000"
OUTPUT = ROOT / "assets" / "questions"

# Page-level clean-ups applied before cropping:
#   ("mirror", (x0, y0, x1, y1), axis_x)  replace the region with its mirror image about axis_x
#                                          (paper tone matched to the band just above the region)
#   ("clean", (x0, y0, x1, y1), sample)   repaint white/green (check-mark) pixels with the median of `sample`
PAGE_FIXES = {
    26: [("mirror", (986, 878, 1004, 952), 930)],                                         # exam 9 q1: check over option 4 ring
    32: [("mirror", (1784, 1132, 1847, 1206), 1724.5)],                              # exam 11 q28: check over the sign's right border
}

# output file: (pdf page, [option 1..4 boxes]) — options are printed right-to-left in two rows.
COMPOSITES = {
    "q-src-ayin1-e06-p17-n01.png": (17, [(1178, 688, 1318, 830), (878, 698, 1010, 832), (1180, 898, 1318, 1030), (872, 893, 1020, 1034)]),
    "q-src-ayin1-e12-p35-n01.png": (35, [(1196, 736, 1338, 880), (852, 736, 995, 880), (1199, 905, 1338, 1046), (877, 912, 983, 1041)]),
    "q-src-ayin1-e13-p38-n01.png": (38, [(1197, 687, 1333, 823), (882, 687, 1007, 823), (1207, 852, 1328, 978), (877, 892, 1028, 953)]),
    "q-src-ayin1-e13-p38-n24.png": (38, [(1952, 232, 2103, 378), (1652, 212, 1761, 378), (1957, 412, 2100, 548), (1642, 397, 1773, 543)]),
    "q-src-ayin1-e03-p08-n01.png": (8, [(1125, 650, 1310, 830), (800, 645, 976, 830), (1130, 850, 1315, 1035), (800, 845, 1000, 1040)]),
    "q-src-ayin1-e08-p23-n06.png": (23, [(535, 1690, 648, 1840), (195, 1690, 315, 1845), (535, 1860, 655, 2010), (190, 1860, 320, 2020)]),
    "q-src-ayin1-e09-p26-n01.png": (26, [(1180, 660, 1335, 815), (850, 660, 1010, 815), (1180, 830, 1335, 990), (850, 830, 1004, 985)]),
    "q-src-ayin1-e10-p29-n01.png": (29, [(1140, 680, 1295, 835), (800, 680, 950, 835), (1138, 852, 1297, 995), (830, 850, 952, 1005)]),
    "q-src-ayin1-e11-p32-n01.png": (32, [(1195, 665, 1340, 810), (865, 660, 1030, 815), (1205, 835, 1325, 975), (870, 830, 1030, 975)]),
    "q-src-ayin1-e01-p02-n02.png": (2, [(528, 576, 700, 748), (200, 576, 380, 748), (528, 778, 700, 946), (198, 774, 373, 946)]),  # old crop had a flat patch where the check was
}

# output file: (pdf page, box) — a single stimulus without option text or check marks.
SINGLES = {
    "q-src-ayin1-e08-p23-n27.png": (23, (2257, 1168, 2328, 1395)),   # flashing-red traffic light
    "q-src-ayin1-e11-p32-n28.png": (32, (1615, 1045, 1846, 1256)),   # merge-from-right sign
    "q-src-ayin1-e11-p32-n29.png": (32, (2268, 1532, 2356, 1780)),   # traffic light only (old crop: cut light + option text)
}


def render(page):
    path = RENDERS / f"page-{page:03d}.png"
    if not path.exists():
        subprocess.run(["swift", str(ROOT / "scripts" / "render_pdf_pages.swift"), str(PDF), str(page), str(page), str(RENDERS), "3000"], check=True)
    image = Image.open(path).convert("RGB")
    array = np.asarray(image).copy()
    for fix in PAGE_FIXES.get(page, []):
        kind, (x0, y0, x1, y1) = fix[0], fix[1]
        if kind == "mirror":
            axis = fix[2]
            mirror_x = lambda x: int(round(2 * axis - x))  # axis fitted on the border centres of both sides
            mirrored = np.stack([array[y0:y1, mirror_x(x)] for x in range(x0, x1)], axis=1).astype(int)
            # Match the paper tone: the mirror side of a photographed page is lit differently.
            band = slice(max(0, y0 - 20), y0)
            target = np.median(array[band, x0:x1].reshape(-1, 3), axis=0)
            source = np.median(np.stack([array[band, mirror_x(x)] for x in range(x0, x1)], axis=1).reshape(-1, 3), axis=0)
            not_red = (mirrored[..., 0] - mirrored[..., 1]) < 40
            mirrored[not_red] += (target - source).astype(int)
            array[y0:y1, x0:x1] = np.clip(mirrored, 0, 255).astype(np.uint8)
        elif kind == "clean":
            sx0, sy0, sx1, sy1 = fix[2]
            colour = np.median(array[sy0:sy1, sx0:sx1].reshape(-1, 3), axis=0).astype(np.uint8)
            region = array[y0:y1, x0:x1].astype(int)
            red, green, blue = region[..., 0], region[..., 1], region[..., 2]
            check_like = (region.min(axis=2) > 170) | (green - red > 12)
            array[y0:y1, x0:x1][check_like] = colour
    return Image.fromarray(array)


def option_composite(source, boxes):
    """Same layout as scripts/extraction/crop_ayin1_exam6.py: option 1 top-right, 2 top-left, 3 bottom-right, 4 bottom-left."""
    canvas = Image.new("RGB", (500, 390), "white")
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 28)
    positions = [(275, 15), (15, 15), (275, 205), (15, 205)]
    draw = ImageDraw.Draw(canvas)
    for number, (box, (x, y)) in enumerate(zip(boxes, positions), start=1):
        option = source.crop(box)
        option.thumbnail((175, 160))
        canvas.paste(option, (x + (175 - option.width) // 2, y + 18 + (160 - option.height) // 2))
        draw.text((x + 195, y + 78), str(number), fill="black", font=font)
    return canvas


def main():
    pages = {}
    for name, (page, boxes) in COMPOSITES.items():
        pages.setdefault(page, render(page))
        option_composite(pages[page], boxes).save(OUTPUT / name, optimize=True)
    for name, (page, box) in SINGLES.items():
        pages.setdefault(page, render(page))
        pages[page].crop(box).save(OUTPUT / name, optimize=True)
    print(f"saved {len(COMPOSITES)} option composites and {len(SINGLES)} single crops")


if __name__ == "__main__":
    main()
