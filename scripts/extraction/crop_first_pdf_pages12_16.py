from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[2]
PAGES = ROOT / "tmp" / "pdfs" / "first-pdf-pages-11-16"
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
            tile = source.crop(box).convert("RGB")
            tile = ImageOps.contain(tile, (160, 145))
            left = 15 + (index - 1) * 185 + (160 - tile.width) // 2
            top = 5 + (145 - tile.height) // 2
            canvas.paste(tile, (left, top))
            draw.rectangle((15 + (index - 1) * 185, 2, 175 + (index - 1) * 185, 182), outline="#d7dbe2", width=2)
            draw.text((92 + (index - 1) * 185, 164), str(index), fill="black", anchor="mm")
    canvas.save(output_path(page, number), optimize=True)


# Page 12 — option-image questions are rebuilt from isolated tiles so the red
# answer labels printed in the source never become part of the question asset.
option_strip(12, 1, [
    (1280, 448, 1388, 521),
    (1140, 448, 1242, 521),
    (1012, 448, 1115, 521),
    (878, 448, 978, 521),
])
crop(12, 2, (124, 448, 232, 550))
crop(12, 3, (790, 606, 878, 688))
crop(12, 4, (124, 606, 234, 700))
crop(12, 5, (792, 755, 916, 860))
option_strip(12, 6, [
    (638, 755, 758, 868),
    (493, 755, 622, 868),
    (345, 755, 476, 868),
    (208, 755, 323, 868),
])
crop(12, 7, (776, 1010, 948, 1100))
crop(12, 9, (786, 1166, 950, 1312))
crop(12, 11, (774, 1312, 996, 1418))

# Page 14.
option_strip(14, 1, [
    (1280, 450, 1392, 552),
    (1138, 450, 1250, 552),
    (996, 450, 1110, 552),
    (856, 450, 968, 552),
])
crop(14, 2, (124, 448, 236, 556))
crop(14, 3, (792, 602, 910, 714))
crop(14, 4, (128, 604, 238, 714))
crop(14, 5, (786, 818, 912, 910))
option_strip(14, 6, [
    (602, 816, 718, 916),
    (476, 816, 590, 916),
    (340, 816, 462, 916),
    (210, 816, 330, 916),
])
crop(14, 7, (778, 972, 922, 1100))
crop(14, 9, (786, 1205, 850, 1358))

# Page 16.
option_strip(16, 1, [
    (1280, 450, 1388, 568),
    (1134, 450, 1250, 568),
    (984, 450, 1112, 568),
    (836, 450, 966, 568),
])
crop(16, 2, (122, 422, 260, 552))
crop(16, 3, (776, 604, 908, 716))
crop(16, 4, (122, 618, 262, 708))
crop(16, 5, (778, 770, 908, 882))
option_strip(16, 6, [
    (618, 792, 754, 866),
    (470, 792, 606, 866),
    (320, 792, 458, 866),
    (152, 792, 292, 866),
])
crop(16, 7, (782, 954, 958, 1100))
crop(16, 11, (785, 1448, 950, 1552))
