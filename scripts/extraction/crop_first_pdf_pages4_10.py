from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tmp" / "pdfs" / "first-pdf-pages-4-10"
OUTPUT = ROOT / "assets" / "questions"

# Each box contains only the illustration needed to answer the question. The
# red answer text printed elsewhere on the source page is deliberately omitted.
BOXES = {
    (4, 3): (815, 650, 950, 755),
    (4, 4): (125, 650, 255, 755),
    (4, 5): (820, 810, 930, 885),
    (4, 6): (125, 815, 255, 915),
    (4, 13): (795, 1490, 970, 1605),
    (5, 19): (775, 465, 1105, 585),
    (6, 2): (120, 440, 255, 575),
    (6, 3): (790, 665, 970, 775),
    (6, 4): (120, 665, 260, 790),
    (6, 7): (800, 1060, 1010, 1165),
    (6, 8): (115, 1050, 190, 1150),
    (6, 9): (785, 1250, 1055, 1335),
    (6, 12): (115, 1380, 240, 1455),
    (7, 25): (810, 1080, 935, 1205),
    (8, 2): (120, 440, 255, 580),
    (8, 3): (790, 620, 945, 735),
    (8, 4): (120, 665, 255, 795),
    (8, 5): (790, 785, 930, 920),
    (8, 7): (760, 1035, 820, 1170),
    (8, 8): (115, 1025, 460, 1105),
    (9, 29): (790, 1780, 950, 1915),
    (10, 1): (790, 435, 940, 575),
    (10, 2): (120, 435, 260, 555),
    (10, 4): (120, 570, 255, 700),
    (10, 9): (805, 1100, 930, 1210),
    (10, 10): (115, 1150, 430, 1265),
    (10, 11): (790, 1360, 1040, 1485),
}

COMPOSITES = {
    (4, 1): [(1260, 465, 1395, 555), (1110, 465, 1240, 555), (960, 465, 1095, 555), (805, 465, 945, 555)],
    (4, 2): [(610, 465, 705, 555), (505, 465, 600, 555), (400, 465, 495, 555), (285, 465, 385, 555)],
    (4, 10): [(610, 1160, 700, 1225), (500, 1160, 600, 1225), (345, 1160, 485, 1225), (115, 1160, 325, 1225)],
    (6, 1): [(1290, 465, 1400, 565), (1130, 465, 1255, 565), (965, 465, 1095, 565), (800, 465, 925, 565)],
    (6, 5): [(1280, 875, 1405, 945), (1110, 875, 1245, 945), (945, 875, 1080, 945), (785, 875, 915, 945)],
    (6, 6): [(575, 875, 700, 945), (425, 875, 560, 945), (270, 875, 410, 945), (115, 875, 250, 945)],
    (8, 1): [(1280, 465, 1405, 560), (1115, 465, 1250, 560), (950, 465, 1085, 560), (790, 465, 925, 560)],
    (8, 6): [(575, 875, 700, 930), (425, 875, 560, 930), (270, 875, 410, 930), (115, 875, 250, 930)],
    (10, 5): [(1265, 755, 1405, 805), (1105, 755, 1245, 805), (945, 755, 1085, 805), (785, 755, 925, 805)],
    (10, 6): [(570, 755, 700, 805), (420, 755, 555, 805), (265, 755, 405, 805), (110, 755, 250, 805)],
}

EXTERNAL_COMPOSITES = {
    (10, 3): (
        OUTPUT / "q-src-600-driveing-p074-n01.png",
        [(5, 135, 140, 225), (5, 45, 140, 125), (160, 135, 290, 225), (160, 45, 292, 125)],
    ),
}


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for (page, number), box in BOXES.items():
        source = SOURCE / f"page-{page:02d}.png"
        destination = OUTPUT / f"q-src-4-5888983329180487891-1-p{page:03d}-n{number:02d}.png"
        with Image.open(source) as image:
            image.convert("RGB").crop(box).save(destination, optimize=True)
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 24)
    for (page, number), tile_boxes in COMPOSITES.items():
        source = SOURCE / f"page-{page:02d}.png"
        destination = OUTPUT / f"q-src-4-5888983329180487891-1-p{page:03d}-n{number:02d}.png"
        canvas = Image.new("RGB", (720, 190), "white")
        draw = ImageDraw.Draw(canvas)
        with Image.open(source) as image:
            rgb = image.convert("RGB")
            for index, tile_box in enumerate(tile_boxes):
                tile = rgb.crop(tile_box)
                tile.thumbnail((150, 135))
                x = 15 + index * 175 + (150 - tile.width) // 2
                canvas.paste(tile, (x, 10 + (135 - tile.height) // 2))
                draw.text((82 + index * 175, 153), str(index + 1), fill="black", font=font, anchor="mm")
        canvas.save(destination, optimize=True)
    for (page, number), (source, tile_boxes) in EXTERNAL_COMPOSITES.items():
        destination = OUTPUT / f"q-src-4-5888983329180487891-1-p{page:03d}-n{number:02d}.png"
        canvas = Image.new("RGB", (720, 190), "white")
        draw = ImageDraw.Draw(canvas)
        with Image.open(source) as image:
            rgb = image.convert("RGB")
            for index, tile_box in enumerate(tile_boxes):
                tile = rgb.crop(tile_box)
                tile.thumbnail((150, 135))
                x = 15 + index * 175 + (150 - tile.width) // 2
                canvas.paste(tile, (x, 10 + (135 - tile.height) // 2))
                draw.text((82 + index * 175, 153), str(index + 1), fill="black", font=font, anchor="mm")
        canvas.save(destination, optimize=True)
    print(f"saved {len(BOXES) + len(COMPOSITES) + len(EXTERNAL_COMPOSITES)} question assets")


if __name__ == "__main__":
    main()
