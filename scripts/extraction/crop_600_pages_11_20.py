from pathlib import Path

from PIL import Image


SOURCE = Path("/private/tmp/ayeenname-600-driveing-11-20")
OUTPUT = Path("assets/questions")

# Pixel boxes were selected once from the 1240x1754 page renders. They include
# only the sign/diagram used by the question, never the red answer text.
CROPS = {
    (11, 9): (670, 150, 1020, 315),
    (11, 10): (90, 145, 280, 425),
    (11, 11): (690, 485, 950, 735),
    (11, 12): (75, 460, 305, 655),
    (11, 13): (700, 810, 960, 1065),
    (11, 14): (135, 810, 445, 1055),
    (11, 15): (710, 1120, 1205, 1375),
    (13, 23): (685, 165, 925, 315),
    (13, 28): (150, 1010, 575, 1290),
    (13, 29): (700, 1450, 795, 1665),
    (14, 1): (715, 325, 1185, 565),
    (14, 2): (155, 340, 480, 570),
    (14, 3): (710, 615, 925, 885),
    (14, 4): (95, 640, 385, 885),
    (14, 5): (685, 925, 935, 1190),
    (14, 6): (105, 940, 395, 1220),
    (14, 7): (685, 1185, 930, 1455),
    (14, 8): (75, 1290, 390, 1460),
    (15, 11): (685, 700, 845, 945),
    (17, 23): (685, 215, 930, 455),
    (17, 24): (105, 130, 655, 245),
    (17, 29): (685, 1335, 775, 1560),
    (18, 6): (110, 890, 360, 1155),
    (18, 7): (685, 1180, 910, 1395),
    (18, 8): (95, 1190, 360, 1460),
    (19, 9): (685, 125, 915, 370),
    (19, 10): (135, 140, 380, 380),
    (19, 11): (685, 410, 935, 635),
    (19, 12): (135, 405, 380, 635),
    (19, 14): (95, 660, 390, 930),
    (19, 17): (680, 1320, 950, 1580),
    (20, 19): (675, 100, 855, 290),
    (20, 23): (675, 1180, 1060, 1415),
}


OUTPUT.mkdir(parents=True, exist_ok=True)
for (page, number), box in CROPS.items():
    source = SOURCE / f"page-{page}.pdf.png"
    destination = OUTPUT / f"q-src-600-driveing-p{page:03d}-n{number:02d}.png"
    with Image.open(source) as page_image:
        page_image.crop(box).save(destination, optimize=True)
    print(destination)
