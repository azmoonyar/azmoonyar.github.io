from pathlib import Path
from PIL import Image

SOURCE = Path("/private/tmp/ayeenname-600-driveing-66-75")
OUTPUT = Path("assets/questions")
CROPS = {
    (67, 10): (70, 120, 330, 325), (67, 12): (80, 375, 190, 605),
    (67, 13): (545, 640, 720, 820), (67, 14): (70, 650, 325, 840),
    (67, 15): (545, 920, 710, 1115), (67, 16): (85, 915, 255, 1120),
    (68, 19): (545, 330, 760, 580), (68, 23): (545, 925, 700, 1085),
    (69, 25): (545, 125, 920, 390), (69, 26): (60, 120, 270, 365),
    (69, 27): (545, 430, 720, 620), (69, 28): (55, 400, 310, 665),
    (69, 29): (545, 815, 805, 1080), (69, 30): (100, 790, 445, 1130),
    (70, 1): (535, 175, 740, 365), (70, 4): (175, 425, 440, 645),
    (70, 8): (90, 950, 275, 1150),
}
OUTPUT.mkdir(parents=True, exist_ok=True)
for (page, number), box in CROPS.items():
    with Image.open(SOURCE / f"page-{page}.png") as image:
        image.crop(box).save(OUTPUT / f"q-src-600-driveing-p{page:03d}-n{number:02d}.png", optimize=True)
