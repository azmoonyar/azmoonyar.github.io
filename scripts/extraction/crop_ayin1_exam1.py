#!/usr/bin/env python3
"""Crop only the visual stimulus for image-based questions in exam 1.

No OCR is performed. Coordinates were determined by direct visual inspection.
"""

from pathlib import Path

from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("/private/tmp/ayeenname-ayin1-hi")
OUTPUT = ROOT / "assets" / "questions"

# question: (rendered PDF page, left, top, right, bottom)
CROPS = {
    1: (2, 545, 350, 930, 675),
    2: (2, 95, 345, 490, 675),
    3: (2, 575, 720, 755, 900),
    4: (2, 100, 715, 295, 890),
    5: (2, 545, 1060, 690, 1245),
    6: (2, 85, 1055, 285, 1245),
    7: (3, 1510, 70, 1705, 240),
    8: (3, 1090, 75, 1430, 225),
    11: (3, 1535, 710, 1705, 940),
    23: (2, 1590, 180, 1750, 315),
    24: (2, 1100, 82, 1475, 195),
    29: (2, 1550, 1070, 1690, 1310),
}


def trim_white(image: Image.Image, pad: int = 16) -> Image.Image:
    rgb = image.convert("RGB")
    pixels = rgb.load()
    xs, ys = [], []
    for y in range(rgb.height):
        for x in range(rgb.width):
            r, g, b = pixels[x, y]
            if min(r, g, b) < 225 or max(r, g, b) - min(r, g, b) > 24:
                xs.append(x)
                ys.append(y)
    if not xs:
        return rgb
    box = (
        max(0, min(xs) - pad),
        max(0, min(ys) - pad),
        min(rgb.width, max(xs) + pad + 1),
        min(rgb.height, max(ys) + pad + 1),
    )
    return rgb.crop(box)


def remove_green_answer_marks(image: Image.Image) -> Image.Image:
    """Paint over the source's green answer stamps without touching sign artwork."""
    rgb = image.convert("RGB")
    pixels = rgb.load()
    marked = []
    for y in range(rgb.height):
        for x in range(rgb.width):
            r, g, b = pixels[x, y]
            if g > 95 and g - r > 38 and g - b > 22:
                marked.append((x, y))
    if not marked:
        return rgb
    x0 = max(0, min(x for x, _ in marked) - 10)
    y0 = max(0, min(y for _, y in marked) - 10)
    x1 = min(rgb.width, max(x for x, _ in marked) + 11)
    y1 = min(rgb.height, max(y for _, y in marked) + 11)
    samples = []
    for y in range(max(0, y0 - 5), min(rgb.height, y1 + 5)):
        for x in range(max(0, x0 - 5), min(rgb.width, x1 + 5)):
            if x0 <= x < x1 and y0 <= y < y1:
                continue
            r, g, b = pixels[x, y]
            if min(r, g, b) > 130:
                samples.append((r, g, b))
    fill = tuple(sorted(channel)[len(channel) // 2] for channel in zip(*samples)) if samples else (225, 224, 164)
    patch = Image.new("RGB", (x1 - x0, y1 - y0), fill)
    rgb.paste(patch, (x0, y0))
    return rgb


OUTPUT.mkdir(parents=True, exist_ok=True)
for number, (page, left, top, right, bottom) in CROPS.items():
    source = SOURCE / f"page-{page:02}.png"
    crop = Image.open(source).convert("RGB").crop((left, top, right, bottom))
    crop = remove_green_answer_marks(crop)
    crop = trim_white(crop)
    crop.save(OUTPUT / f"q-src-ayin1-e01-p{page:02}-n{number:02}.png", optimize=True)

print(f"saved {len(CROPS)} crops")
