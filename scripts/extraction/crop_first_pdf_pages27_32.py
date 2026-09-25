from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[2]
PAGES = ROOT / "tmp" / "pdfs" / "first-pdf-pages-27-32"
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


crop(27, 29, (794, 1324, 994, 1452))

crop(28, 1, (820, 438, 924, 542))
crop(28, 2, (152, 438, 266, 556))
crop(28, 3, (790, 592, 898, 686))
crop(28, 4, (120, 588, 282, 666))
option_strip(28, 5, [
    (1264, 746, 1360, 834),
    (1128, 746, 1230, 834),
    (1004, 746, 1112, 834),
    (886, 746, 988, 834),
])
crop(28, 6, (130, 704, 228, 802))
crop(28, 7, (800, 866, 908, 968))
crop(28, 8, (120, 866, 238, 950))
crop(28, 9, (790, 988, 896, 1098))
crop(28, 10, (120, 982, 232, 1100))
crop(28, 11, (790, 1116, 934, 1250))
crop(28, 13, (788, 1298, 1022, 1474))
crop(28, 14, (98, 1298, 326, 1468))
crop(28, 15, (796, 1494, 998, 1620))
crop(28, 16, (120, 1492, 334, 1618))

crop(29, 25, (782, 1218, 892, 1334))
crop(29, 28, (120, 1528, 370, 1632))

crop(30, 1, (806, 414, 916, 506))
crop(30, 2, (120, 422, 252, 516))
crop(30, 3, (804, 634, 912, 734))
crop(30, 4, (120, 634, 230, 732))
crop(30, 5, (808, 762, 906, 872))
crop(30, 6, (120, 764, 208, 872))
option_strip(30, 7, [
    (1260, 938, 1368, 1040),
    (1126, 938, 1234, 1040),
    (992, 938, 1102, 1040),
    (850, 938, 966, 1040),
])
crop(30, 8, (120, 930, 246, 1030))
crop(30, 9, (796, 1078, 906, 1188))
option_strip(30, 10, [
    (634, 1122, 752, 1224),
    (508, 1122, 620, 1224),
    (382, 1122, 494, 1224),
    (250, 1122, 368, 1224),
])
crop(30, 11, (804, 1256, 912, 1358))
option_strip(30, 12, [
    (634, 1300, 752, 1408),
    (508, 1300, 620, 1408),
    (380, 1300, 494, 1408),
    (246, 1300, 368, 1408),
])
crop(30, 13, (796, 1494, 948, 1624))
crop(30, 14, (112, 1450, 210, 1558))
crop(30, 15, (798, 1686, 970, 1800))

option_strip(31, 18, [
    (674, 222, 778, 334),
    (580, 222, 660, 334),
    (452, 222, 560, 334),
    (320, 222, 434, 334),
])
option_strip(31, 21, [
    (1260, 610, 1382, 708),
    (1124, 610, 1242, 708),
    (1000, 610, 1110, 708),
    (884, 610, 986, 708),
])
option_strip(31, 22, [
    (650, 612, 766, 706),
    (520, 612, 632, 706),
    (388, 612, 506, 706),
    (258, 612, 372, 706),
])
crop(31, 23, (792, 738, 912, 842))
crop(31, 24, (120, 738, 238, 842))
crop(31, 25, (796, 866, 912, 972))
crop(31, 27, (794, 1054, 914, 1162))
crop(31, 28, (120, 1054, 232, 1164))
crop(31, 29, (796, 1202, 912, 1312))
option_strip(31, 30, [
    (666, 1242, 770, 1338),
    (530, 1242, 640, 1338),
    (396, 1242, 506, 1338),
    (260, 1242, 374, 1338),
])

# Page 32 uses a slightly different page canvas (1530 x 1980).
crop(32, 1, (770, 322, 996, 524))
crop(32, 4, (120, 692, 202, 898))
