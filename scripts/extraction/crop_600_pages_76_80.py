from pathlib import Path
from PIL import Image

SOURCE = Path("/private/tmp/ayeenname-600-driveing-76-80")
OUTPUT = Path("assets/questions")
CROPS = {
    (76, 17): (535, 105, 770, 260),
    (77, 26): (75, 140, 220, 285), (77, 27): (535, 495, 800, 745),
    (77, 28): (55, 485, 270, 735), (77, 29): (535, 825, 790, 1085),
    (77, 30): (65, 825, 350, 1140),
    (78, 3): (535, 390, 690, 630), (78, 4): (55, 390, 300, 665),
    (78, 5): (535, 670, 680, 920),
    (79, 9): (535, 90, 790, 340), (79, 10): (55, 90, 305, 350),
    (79, 11): (530, 405, 790, 670), (79, 14): (65, 815, 400, 1050),
    (79, 16): (90, 1050, 370, 1305),
    (80, 23): (535, 970, 705, 1160), (80, 24): (65, 970, 430, 1240),
}

OUTPUT.mkdir(parents=True, exist_ok=True)
for (page, number), box in CROPS.items():
    with Image.open(SOURCE / f"page-{page}.png") as image:
        image.crop(box).save(OUTPUT / f"q-src-600-driveing-p{page:03d}-n{number:02d}.png", optimize=True)
