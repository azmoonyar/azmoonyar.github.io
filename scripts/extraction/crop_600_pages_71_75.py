from pathlib import Path
from PIL import Image

SOURCE = Path("/private/tmp/ayeenname-600-driveing-66-75")
OUTPUT = Path("assets/questions")
CROPS = {
    (71, 9): (545, 105, 655, 300), (71, 10): (70, 95, 430, 360),
    (71, 11): (545, 400, 735, 650), (71, 12): (50, 400, 255, 650),
    (71, 13): (545, 680, 775, 930), (71, 14): (55, 675, 350, 940),
    (71, 15): (550, 1000, 930, 1205),
    (72, 23): (545, 900, 805, 1100), (72, 24): (70, 920, 405, 1215),
    (73, 26): (80, 335, 205, 595), (73, 28): (55, 375, 300, 635),
    (73, 29): (530, 875, 790, 1130),
    (74, 1): (530, 100, 825, 345), (74, 2): (70, 100, 315, 330),
    (74, 3): (530, 365, 860, 590), (74, 4): (65, 370, 270, 595),
    (74, 7): (545, 850, 850, 1215), (74, 8): (55, 845, 205, 1100),
    (75, 10): (40, 55, 315, 310), (75, 11): (530, 415, 770, 665),
    (75, 12): (45, 420, 315, 665),
}

OUTPUT.mkdir(parents=True, exist_ok=True)
for (page, number), box in CROPS.items():
    with Image.open(SOURCE / f"page-{page}.png") as image:
        image.crop(box).save(OUTPUT / f"q-src-600-driveing-p{page:03d}-n{number:02d}.png", optimize=True)
