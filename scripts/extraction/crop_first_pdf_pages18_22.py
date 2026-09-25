from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[2]
PAGES = ROOT / "tmp" / "pdfs" / "first-pdf-pages-17-22"
OUT = ROOT / "assets" / "questions"
OUT.mkdir(parents=True, exist_ok=True)


def output_path(page: int, number: int) -> Path:
    return OUT / f"q-src-4-5888983329180487891-1-p{page:03d}-n{number:02d}.png"


def crop(page: int, number: int, box: tuple[int, int, int, int]) -> None:
    with Image.open(PAGES / f"page-{page}.png") as source:
        source.crop(box).save(output_path(page, number), optimize=True)


def option_strip(page: int, number: int, boxes: list[tuple[int, int, int, int]]) -> None:
    canvas = Image.new("RGB", (760, 190), "white")
    draw = ImageDraw.Draw(canvas)
    with Image.open(PAGES / f"page-{page}.png") as source:
        for index, box in enumerate(boxes, start=1):
            tile = ImageOps.contain(source.crop(box).convert("RGB"), (160, 145))
            slot_left = 15 + (index - 1) * 185
            left = slot_left + (160 - tile.width) // 2
            top = 5 + (145 - tile.height) // 2
            canvas.paste(tile, (left, top))
            draw.rectangle((slot_left, 2, slot_left + 160, 182), outline="#d7dbe2", width=2)
            draw.text((slot_left + 80, 164), str(index), fill="black", anchor="mm")
    canvas.save(output_path(page, number), optimize=True)


def labeled_strip(page: int, number: int, boxes: list[tuple[int, int, int, int]], labels: list[str]) -> None:
    canvas = Image.new("RGB", (570, 190), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype("/System/Library/Fonts/GeezaPro.ttc", 28)
    with Image.open(PAGES / f"page-{page}.png") as source:
        for index, (box, label) in enumerate(zip(boxes, labels)):
            tile = ImageOps.contain(source.crop(box).convert("RGB"), (155, 135))
            slot_left = 15 + index * 185
            canvas.paste(tile, (slot_left + (155 - tile.width) // 2, 5 + (135 - tile.height) // 2))
            draw.rectangle((slot_left, 2, slot_left + 155, 182), outline="#d7dbe2", width=2)
            draw.text((slot_left + 77, 160), label, font=font, fill="black", anchor="mm")
    canvas.save(output_path(page, number), optimize=True)


# Page 18 / exam 9.
crop(18, 1, (780, 414, 908, 532))
crop(18, 2, (124, 420, 236, 526))
crop(18, 3, (780, 540, 908, 646))
crop(18, 4, (124, 540, 246, 646))
crop(18, 5, (786, 692, 908, 818))
option_strip(18, 6, [
    (638, 692, 758, 800),
    (488, 692, 612, 800),
    (316, 692, 468, 800),
    (156, 692, 294, 800),
])
crop(18, 7, (780, 902, 930, 1042))
crop(18, 8, (118, 848, 252, 976))
crop(18, 9, (786, 1162, 910, 1242))
crop(18, 14, (120, 1558, 430, 1778))

# Page 19 continuation.
crop(19, 29, (784, 1524, 948, 1588))

# Page 20 / exam 10.
option_strip(20, 1, [
    (1270, 448, 1392, 532),
    (1120, 448, 1240, 532),
    (970, 448, 1090, 532),
    (808, 448, 940, 532),
])
crop(20, 2, (140, 444, 260, 566))
crop(20, 3, (796, 610, 932, 714))
crop(20, 4, (136, 614, 248, 714))
crop(20, 5, (788, 738, 918, 868))
option_strip(20, 6, [
    (630, 766, 760, 884),
    (478, 766, 618, 884),
    (332, 766, 468, 884),
    (164, 766, 304, 884),
])
crop(20, 7, (784, 968, 1014, 1118))
crop(20, 8, (116, 926, 306, 1046))
crop(20, 13, (796, 1734, 874, 1814))

# Page 21 continuation.
labeled_strip(21, 24, [
    (376, 886, 434, 966),
    (290, 886, 352, 966),
    (204, 886, 272, 966),
], ["فلا", "ب", "ج"])

# Page 22 / exam 11.
crop(22, 1, (802, 448, 930, 564))
crop(22, 2, (94, 444, 216, 548))
crop(22, 3, (796, 592, 910, 710))
crop(22, 4, (92, 598, 168, 708))
crop(22, 5, (796, 716, 930, 842))
crop(22, 6, (66, 718, 192, 840))
crop(22, 8, (180, 906, 320, 1014))
crop(22, 9, (808, 1096, 1144, 1262))
crop(22, 10, (164, 1086, 350, 1210))
crop(22, 12, (76, 1320, 274, 1574))
