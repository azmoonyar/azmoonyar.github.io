#!/usr/bin/env python3
"""Regenerate the eight 4-option sign composites of 4_5888983329180487891-1.pdf.

The tile boxes in crop_first_pdf_pages4_10.py were offset, so several tiles showed
halves of two signs, blank space, or the red «گزینه» answer label. The boxes below
were measured visually on the rendered source pages (tmp/pdfs/first-pdf-pages-4-10,
1489 x 2105 px) with a coordinate ruler; each one holds exactly one option sign and
stops above the «گزینه N» label, so the red answer label is never included.
Output file names are unchanged, so question data is untouched. No OCR is involved.

usage: fix_option_grid_assets.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tmp" / "pdfs" / "first-pdf-pages-4-10"
OUTPUT = ROOT / "assets" / "questions"

# (page, question): option 1..4 boxes (left, top, right, bottom). Options are printed
# right-to-left on the page, so option 1 is the right-most sign.
TILES = {
    (4, 1): [(1262, 448, 1368, 551), (1143, 448, 1238, 551), (1013, 448, 1114, 551), (885, 448, 984, 551)],
    (4, 2): [(661, 448, 770, 551), (533, 448, 649, 551), (420, 448, 520, 551), (301, 448, 415, 551)],
    (4, 10): [(650, 1133, 751, 1207), (508, 1133, 614, 1207), (353, 1133, 480, 1207), (128, 1133, 336, 1207)],
    (6, 5): [(1206, 864, 1346, 955), (1078, 864, 1196, 955), (961, 864, 1074, 955), (825, 864, 960, 955)],
    (6, 6): [(646, 864, 772, 958), (489, 864, 629, 958), (314, 864, 455, 958), (165, 864, 298, 958)],
    (8, 6): [(648, 826, 774, 934), (515, 823, 630, 934), (388, 826, 505, 934), (253, 826, 370, 934)],
    (10, 5): [(1264, 733, 1344, 808), (1160, 733, 1240, 808), (1053, 733, 1134, 808), (946, 733, 1017, 808)],
    (10, 6): [(638, 741, 752, 821), (489, 741, 600, 821), (342, 741, 444, 821), (202, 733, 292, 821)],
}


def compose(page_image, tiles, destination):
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 24)
    canvas = Image.new("RGB", (720, 190), "white")
    draw = ImageDraw.Draw(canvas)
    for index, box in enumerate(tiles):
        tile = page_image.crop(box)
        tile.thumbnail((150, 135))
        x = 15 + index * 175 + (150 - tile.width) // 2
        canvas.paste(tile, (x, 10 + (135 - tile.height) // 2))
        draw.text((82 + index * 175, 153), str(index + 1), fill="black", font=font, anchor="mm")
    canvas.save(destination, optimize=True)


def main():
    for (page, number), tiles in TILES.items():
        with Image.open(SOURCE / f"page-{page:02d}.png") as image:
            rgb = image.convert("RGB")
        destination = OUTPUT / f"q-src-4-5888983329180487891-1-p{page:03d}-n{number:02d}.png"
        compose(rgb, tiles, destination)
    print(f"regenerated {len(TILES)} option composites")


if __name__ == "__main__":
    main()
