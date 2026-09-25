from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[2]
PAGES = ROOT / "tmp" / "pdfs" / "600-pages-6-10-review"
OUT = ROOT / "assets" / "questions"
OUT.mkdir(parents=True, exist_ok=True)


def source_path(page: int) -> Path:
    return PAGES / f"page-{page:02d}.png"


def output_path(page: int, number: int) -> Path:
    return OUT / f"q-src-600-driveing-p{page:03d}-n{number:02d}.png"


def crop(page: int, number: int, box: tuple[int, int, int, int]) -> None:
    with Image.open(source_path(page)) as source:
        source.crop(box).save(output_path(page, number), optimize=True)


def option_strip(page: int, number: int, boxes: list[tuple[int, int, int, int]]) -> None:
    canvas = Image.new("RGB", (760, 190), "white")
    draw = ImageDraw.Draw(canvas)
    with Image.open(source_path(page)) as source:
        for index, box in enumerate(boxes, start=1):
            tile = ImageOps.contain(source.crop(box).convert("RGB"), (160, 145))
            slot_left = 15 + (index - 1) * 185
            canvas.paste(tile, (slot_left + (160 - tile.width) // 2, 5 + (145 - tile.height) // 2))
            draw.rectangle((slot_left, 2, slot_left + 160, 182), outline="#d7dbe2", width=2)
            draw.text((slot_left + 80, 164), str(index), fill="black", anchor="mm")
    canvas.save(output_path(page, number), optimize=True)


# Source answer stars/red option text are kept outside the crops.
crop(6, 1, (654, 220, 878, 444))
crop(6, 8, (98, 1128, 474, 1254))
crop(8, 19, (640, 930, 820, 1042))
crop(9, 23, (694, 210, 842, 342))
crop(9, 24, (68, 218, 254, 294))
crop(9, 25, (668, 462, 894, 652))
crop(9, 26, (88, 444, 344, 678))
option_strip(9, 27, [
    (898, 940, 1018, 1054),
    (688, 940, 818, 1054),
    (898, 1088, 1018, 1182),
    (688, 1088, 818, 1182),
])
option_strip(9, 28, [
    (376, 924, 516, 1058),
    (168, 924, 304, 1058),
    (376, 1066, 502, 1182),
    (168, 1066, 304, 1182),
])
crop(9, 29, (692, 1284, 906, 1498))
crop(9, 30, (96, 1246, 384, 1482))
crop(10, 8, (98, 1138, 526, 1322))
