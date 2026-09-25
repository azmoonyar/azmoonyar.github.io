from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[2]
PAGES = ROOT / "tmp" / "pdfs" / "first-pdf-pages-23-26"
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
            canvas.paste(tile, (slot_left + (160 - tile.width) // 2, 5 + (145 - tile.height) // 2))
            draw.rectangle((slot_left, 2, slot_left + 160, 182), outline="#d7dbe2", width=2)
            draw.text((slot_left + 80, 164), str(index), fill="black", anchor="mm")
    canvas.save(output_path(page, number), optimize=True)


crop(23, 28, (84, 1420, 232, 1566))

crop(24, 1, (774, 414, 900, 538))
crop(24, 2, (122, 412, 228, 504))
crop(24, 3, (772, 558, 892, 680))
crop(24, 4, (120, 562, 232, 662))
crop(24, 5, (774, 690, 908, 808))
crop(24, 6, (128, 692, 242, 800))
crop(24, 7, (778, 838, 920, 960))
crop(24, 8, (120, 830, 238, 950))
crop(24, 15, (782, 1664, 886, 1760))

crop(25, 19, (774, 410, 912, 472))

crop(26, 1, (790, 416, 898, 520))
crop(26, 2, (120, 414, 224, 520))
crop(26, 3, (796, 544, 908, 660))
option_strip(26, 4, [
    (636, 564, 754, 666),
    (504, 564, 624, 666),
    (360, 564, 480, 666),
    (222, 564, 330, 666),
])
crop(26, 5, (790, 710, 908, 824))
crop(26, 6, (122, 712, 220, 804))
crop(26, 7, (786, 828, 904, 946))
crop(26, 8, (122, 836, 232, 940))
crop(26, 9, (790, 950, 910, 1068))
crop(26, 10, (122, 952, 224, 1064))
crop(26, 12, (108, 1078, 296, 1180))
option_strip(26, 13, [
    (1262, 1312, 1352, 1384),
    (1152, 1312, 1240, 1384),
    (1022, 1312, 1110, 1384),
    (822, 1312, 978, 1384),
])
crop(26, 14, (122, 1236, 186, 1324))
