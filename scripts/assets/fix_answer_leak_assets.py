#!/usr/bin/env python3
"""Remove answer markers that the source PDFs print next to the correct option.

600-driveing.pdf marks the answer with an asterisk (red or black) or a check mark and
ایین نامه-1.pdf with a green check; some question crops still contained that marker, or a
fragment of the correct option's text next to it, so the picture revealed the answer.
Every box below was located visually with a coordinate ruler (and checked against a pixel map). File names
are unchanged, so no question data changes. No OCR is involved.

usage: fix_answer_leak_assets.py [--dry-run OUT_DIR]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets" / "questions"
ORIGINALS = ROOT / "tmp" / "asset-originals"  # untouched copies, so re-running never compounds crops
P600 = "q-src-600-driveing-"

# file -> list of operations applied in order:
#   ("mask", box, fill)  fill = "ring" (median of a thin ring around the box),
#                         "paper" (same, ignoring near-white and green pixels: photographed pages),
#                         "page" (median of the image border: the pale-yellow page colour),
#                         ("sample", box) (median colour of a clean background box nearby),
#                         "blend" (column-wise interpolation between the background just above and
#                                  below the box, so shaded photo backgrounds stay continuous)
#   ("crop", box)         keep only the box (None = image edge)
FIXES = {
    f"{P600}p011-n15.png": [("mask", (428, 93, 456, 114), "ring")],          # black asterisk by option 1
    f"{P600}p014-n02.png": [("mask", (131, 130, 151, 153), "ring")],         # red asterisk by option 3
    f"{P600}p022-n02.png": [("mask", (196, 126, 220, 146), "ring")],         # red asterisk by option 4
    f"{P600}p037-n30.png": [("mask", (163, 44, 180, 63), "ring")],           # red asterisk by option 2
    f"{P600}p041-n25.png": [("mask", (162, 165, 190, 187), "ring")],         # red asterisk by option 4
    f"{P600}p041-n29.png": [("mask", (394, 363, 430, 391), "ring")],         # red asterisk by option 3
    f"{P600}p043-n15.png": [("mask", (155, 38, 168, 57), "ring")],           # red asterisk fragment in tile 1
    f"{P600}p048-n24.png": [("mask", (256, 86, 291, 118), "page")],          # black asterisk by option 2
    f"{P600}p049-n27.png": [("mask", (405, 202, 459, 258), "paper")],        # check mark by option 3
    f"{P600}p051-n10.png": [("mask", (168, 40, 202, 80), "page")],           # black asterisk by option 2
    f"{P600}p052-n23.png": [("crop", (0, 8, 302, 192))],                     # option-text fragments beside the figure
    f"{P600}p053-n30.png": [("mask", (343, 52, 361, 74), "ring")],           # red asterisk by option 1
    f"{P600}p055-n10.png": [("mask", (362, 216, 401, 257), "page"), ("crop", (0, 18, 430, 314))],  # check mark + other questions' text
    f"{P600}p055-n15.png": [("mask", (276, 20, 300, 42), "ring")],           # black asterisk by option 1
    f"{P600}p060-n15.png": [("mask", (156, 127, 181, 150), "ring")],         # red asterisk by option 4
    f"{P600}p060-n24.png": [("mask", (146, 63, 162, 80), "ring")],           # red asterisk by option 2
    f"{P600}p065-n30.png": [("mask", (361, 237, 382, 258), "ring")],         # red asterisk by option 3
    f"{P600}p069-n25.png": [("mask", (161, 31, 183, 52), "ring")],           # red asterisk by option 2
    f"{P600}p069-n30.png": [("mask", (322, 120, 342, 141), "ring")],         # red asterisk by option 1
    f"{P600}p071-n15.png": [("mask", (301, 59, 331, 97), "blend")],           # check mark by option 1
    f"{P600}p074-n01.png": [("mask", (104, 72, 124, 98), "page")],           # black asterisk by option 2
    f"{P600}p074-n03.png": [("mask", (240, 54, 283, 100), "blend")],          # check mark by option 1
    f"{P600}p079-n14.png": [("mask", (186, 27, 202, 44), "ring"), ("crop", (0, 0, 335, 212))],  # asterisk by option 2 + other question's text
    "q-src-ayin1-e11-p32-n04.png": [("crop", (0, 0, None, 158))],               # sign only: drops option text + check
    "q-src-ayin1-e02-p05-n23.png": [("crop", (0, 0, None, 150))],               # figure only: drops option text + check
    "q-src-ayin1-e05-p14-n24.png": [("crop", (18, 10, 298, 200))],              # photo only: dropped «۱ و ۲ با هم» (text of the keyed option)
    "q-src-ayin1-e05-p14-n29.png": [("crop", (0, 95, 201, 300))],               # figure only: dropped option-line fragments
}
# Figures whose crop also held the option list with its answer marker ("*" and red text), or the
# text of a neighbouring question: keep the figure only. Boxes = figure bounds measured on a
# pixel map (the marker sits 1-2 px right of the figure on p035, p047, p060 and p065).
FIGURE_ONLY = {
    "p015-n11": (1, 9, 145, 239), "p017-n23": (10, 7, 239, 240), "p035-n12": (5, 15, 414, 224),
    "p037-n26": (5, 3, 417, 169), "p046-n08": (0, 0, 465, 100), "p047-n09": (6, 2, 425, 124),
    "p049-n30": (6, 41, 351, 385), "p051-n13": (0, 6, 257, 262), "p053-n27": (0, 40, 238, 239),
    "p059-n12": (4, 29, 151, 184), "p060-n23": (0, 46, 130, 209), "p063-n16": (0, 24, 165, 113),
    "p064-n23": (0, 26, 133, 156), "p065-n27": (0, 44, 163, 208), "p071-n09": (0, 63, 66, 182),
    "p071-n11": (0, 39, 163, 192), "p072-n23": (0, 23, 155, 153), "p073-n29": (0, 14, 212, 216),
    "p074-n07": (11, 214, 266, 365), "p075-n11": (0, 48, 211, 231), "p077-n27": (4, 78, 234, 250),
    "p080-n23": (0, 36, 132, 174), "p080-n24": (33, 36, 338, 266), "p083-n12": (9, 13, 98, 209),
    "p084-n23": (17, 0, 146, 74), "p084-n24": (24, 0, 404, 56),
    # option text of other choices beside the figure (not the answer, but noise that invites guessing)
    "p022-n07": (9, 16, 118, 284), "p027-n09": (0, 3, 153, 181), "p033-n24": (19, 22, 232, 301),
    "p048-n23": (10, 24, 411, 179), "p051-n09": (8, 3, 310, 118), "p052-n24": (18, 0, 533, 148),
    "p053-n25": (0, 8, 217, 169), "p064-n24": (0, 56, 209, 196), "p074-n08": (1, 28, 114, 233),
    "p075-n12": (12, 45, 248, 215), "p076-n17": (1, 3, 192, 139), "p078-n05": (4, 36, 84, 199),
    "p079-n16": (19, 15, 228, 193),
}
FIXES.update({f"{P600}{key}.png": [("crop", box)] for key, box in FIGURE_ONLY.items()})
# tablo.pdf / 4_5888 crops that caught a strip of the next sign or of option text at one edge.
FIXES.update({
    "q-src-tablo-p034-n006.png": [("crop", (0, 0, 336, 300))],
    "q-src-tablo-p070-n135.png": [("crop", (0, 0, 234, 205))],
    "q-src-tablo-p096-n230.png": [("crop", (0, 20, 242, 300))],
    "q-src-tablo-p101-n246.png": [("crop", (0, 0, 343, 338))],
    "q-src-tablo-p113-n287.png": [("crop", (0, 0, 342, 338))],
    "q-src-4-5888983329180487891-1-p002-n07.png": [("crop", (0, 0, 168, 147))],
    "q-src-4-5888983329180487891-1-p013-n25.png": [("crop", (0, 27, 109, 160))],
    f"{P600}p079-n09.png": [("mask", (164, 206, 178, 219), (255, 255, 255)), ("crop", (4, 24, 182, 219))],  # drawing box only; one option-text stroke overlapped it
    f"{P600}p014-n05.png": [("mask", (160, 162, 175, 184), "page")],
})
# ایین نامه-1 photographed pages: crops that also held option lines (sometimes the keyed one) or
# the text of a neighbouring question. Boxes measured with a ruler on each crop; None = image edge.
AYIN1_FIGURE_ONLY = {
    "e01-p02-n29": (50, 0, 105, 118), "e01-p03-n07": (70, 0, None, 135), "e01-p03-n08": (12, 8, 293, 118),
    "e02-p06-n07": (72, 45, 352, 122), "e02-p06-n08": (22, 38, 120, 132), "e02-p06-n12": (14, 98, 182, None),
    "e03-p08-n04": (42, 44, 142, 165), "e03-p08-n06": (34, 64, 110, 222), "e04-p11-n05": (0, 0, 140, 120),
    "e05-p14-n23": (8, 16, 268, 162), "e05-p15-n07": (10, 10, 128, 170), "e06-p17-n24": (14, 112, 252, None),
    "e06-p17-n30": (10, 90, 78, None), "e06-p18-n07": (0, 45, 118, None), "e07-p21-n08": (4, 24, 112, 132),
    "e08-p23-n03": (14, 10, 182, 192), "e08-p23-n04": (34, 44, 192, 200), "e08-p23-n23": (0, 92, 186, None),
    "e08-p23-n28": (0, 92, 206, 256), "e08-p24-n22": (28, 92, None, None), "e09-p26-n28": (0, 38, 186, None),
    "e09-p27-n07": (24, 58, 200, 192), "e09-p27-n08": (82, 28, None, 142), "e09-p27-n16": (24, 12, 222, 218),
    "e10-p29-n05": (0, 0, 100, None), "e11-p33-n12": (0, 102, 186, None),
}
FIXES.update({f"q-src-ayin1-{key}.png": [("crop", box)] for key, box in AYIN1_FIGURE_ONLY.items()})
# ایین نامه-1 crops with a green check are rebuilt from the page renders by fix_ayin1_option_images.py.


def fill_colour(array, box, mode, width=4):
    left, top, right, bottom = box
    height, full_width = array.shape[:2]
    if isinstance(mode, tuple) and len(mode) == 3 and all(isinstance(v, int) for v in mode):
        return np.array(mode, dtype=np.uint8)  # constant colour, e.g. the white figure background
    if isinstance(mode, tuple) and mode[0] == "sample":
        x0, y0, x1, y1 = mode[1]
        return np.median(array[y0:y1, x0:x1].reshape(-1, 3), axis=0).astype(np.uint8)
    if mode == "page":
        frame = np.concatenate([array[:3].reshape(-1, 3), array[-3:].reshape(-1, 3), array[:, :3].reshape(-1, 3), array[:, -3:].reshape(-1, 3)])
        pixels = frame
    else:
        outer = array[max(0, top - width):min(height, bottom + width), max(0, left - width):min(full_width, right + width)]
        mask = np.ones(outer.shape[:2], bool)
        inner_top, inner_left = top - max(0, top - width), left - max(0, left - width)
        mask[inner_top:inner_top + (bottom - top), inner_left:inner_left + (right - left)] = False
        pixels = outer[mask]
    if mode in ("paper", "page"):
        channels = pixels.astype(int)
        keep = ~((channels.min(axis=1) > 215) | (channels[:, 1] - channels[:, 0] > 25) | (channels.max(axis=1) < 90))
        if keep.any():
            pixels = pixels[keep]
    return np.median(pixels, axis=0).astype(np.uint8)


def usable(pixel):
    """Background sample: not canvas white, not the green check mark, not dark print."""
    red, green, blue = (int(v) for v in pixel)
    return not (min(red, green, blue) > 225 or green - red > 25 or max(red, green, blue) < 90)


def blend(array, box, reach=3):
    """Column-wise interpolation between the background just above and just below the box."""
    left, top, right, bottom = box
    height, width = array.shape[:2]
    fallback = fill_colour(array, box, "paper")
    for x in range(left, right):
        sides = []
        for y0, y1 in ((max(0, top - reach), top), (bottom, min(height, bottom + reach))):
            if y1 > y0:
                sample = np.median(array[y0:y1, max(0, x - 1):min(width, x + 2)].reshape(-1, 3), axis=0)
                if usable(sample):
                    sides.append(sample)
        start, end = (sides[0], sides[-1]) if sides else (fallback, fallback)
        steps = max(1, bottom - top - 1)
        for index, y in enumerate(range(top, bottom)):
            weight = index / steps if len(sides) == 2 else 0.0
            array[y, x] = ((1 - weight) * start + weight * end).astype(np.uint8)
    return array


def apply(image, operations):
    for operation in operations:
        kind, (left, top, right, bottom) = operation[0], operation[1]
        right = image.width if right is None else right
        bottom = image.height if bottom is None else bottom
        if kind == "mask" and operation[2] == "blend":
            image = Image.fromarray(blend(np.asarray(image).copy(), (left, top, right, bottom)))
        elif kind == "mask":
            array = np.asarray(image).copy()
            array[top:bottom, left:right] = fill_colour(array, (left, top, right, bottom), operation[2])
            image = Image.fromarray(array)
        else:
            image = image.crop((left, top, right, bottom))
    return image


def main():
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--dry-run" else ASSETS
    out_dir.mkdir(parents=True, exist_ok=True)
    ORIGINALS.mkdir(parents=True, exist_ok=True)
    for name, operations in FIXES.items():
        original = ORIGINALS / name
        if not original.exists():
            original.write_bytes((ASSETS / name).read_bytes())
        with Image.open(original) as source:
            fixed = apply(source.convert("RGB"), operations)
        fixed.save(out_dir / name, optimize=True)
    print(f"fixed {len(FIXES)} assets -> {out_dir}")


if __name__ == "__main__":
    main()
