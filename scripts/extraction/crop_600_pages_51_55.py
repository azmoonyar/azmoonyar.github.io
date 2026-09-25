from pathlib import Path

from PIL import Image


SOURCE = Path("/private/tmp/ayeenname-600-driveing-51-55")
OUTPUT = Path("assets/questions")

# Coordinates were selected once from direct visual inspection of 1191x1685 renders.
# Each crop includes the complete diagram/sign group while excluding the marked answer.
CROPS = {
    (51, 9): (710, 125, 1080, 260),
    (51, 10): (120, 125, 500, 455),
    (51, 13): (660, 865, 970, 1165),
    (51, 15): (650, 1195, 940, 1455),
    (52, 23): (650, 1000, 1010, 1245),
    (52, 24): (70, 1015, 650, 1225),
    (53, 25): (650, 110, 935, 310),
    (53, 26): (75, 135, 370, 455),
    (53, 27): (650, 485, 955, 765),
    (53, 28): (75, 485, 380, 765),
    (53, 29): (680, 905, 980, 1215),
    (53, 30): (125, 900, 560, 1265),
    (54, 5): (640, 885, 950, 1170),
    (55, 10): (95, 125, 525, 465),
    (55, 15): (710, 1160, 1110, 1515),
    (55, 16): (50, 1160, 350, 1480),
}

OUTPUT.mkdir(parents=True, exist_ok=True)
for (page, number), box in CROPS.items():
    source = SOURCE / f"page-{page}.png"
    destination = OUTPUT / f"q-src-600-driveing-p{page:03d}-n{number:02d}.png"
    with Image.open(source) as page_image:
        page_image.crop(box).save(destination, optimize=True)
    print(destination)
