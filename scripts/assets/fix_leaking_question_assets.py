from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parents[2]
PAGES_600 = ROOT / "tmp" / "pdfs" / "qa-source-600"
PAGES_FIRST = ROOT / "tmp" / "pdfs" / "qa-source-first"
PAGES_TABLO = ROOT / "tmp" / "pdfs" / "qa-source-tablo"
PAGES_AYIN = ROOT / "tmp" / "pdfs" / "qa-source-ayin1"
ASSETS = ROOT / "assets" / "questions"
ASSETS.mkdir(parents=True, exist_ok=True)


def asset_600(page: int, number: int) -> Path:
    return ASSETS / f"q-src-600-driveing-p{page:03d}-n{number:02d}.png"


def asset_first(page: int, number: int) -> Path:
    return ASSETS / f"q-src-4-5888983329180487891-1-p{page:03d}-n{number:02d}.png"


def crop(source: Path, destination: Path, box: tuple[int, int, int, int]) -> None:
    with Image.open(source) as image:
        image.convert("RGB").crop(box).save(destination, optimize=True)


def neutral_strip(
    source: Path,
    destination: Path,
    boxes: list[tuple[int, int, int, int]],
) -> None:
    """Build an answer-neutral option strip from source artwork only."""
    canvas = Image.new("RGB", (760, 190), "white")
    draw = ImageDraw.Draw(canvas)
    with Image.open(source) as image:
        rgb = image.convert("RGB")
        for index, box in enumerate(boxes, start=1):
            tile = ImageOps.contain(rgb.crop(box), (160, 142))
            slot_left = 15 + (index - 1) * 185
            left = slot_left + (160 - tile.width) // 2
            top = 6 + (142 - tile.height) // 2
            canvas.paste(tile, (left, top))
            draw.rectangle((slot_left, 2, slot_left + 160, 182), outline="#d7dbe2", width=2)
            draw.text((slot_left + 80, 164), str(index), fill="black", anchor="mm")
    canvas.save(destination, optimize=True)


def page_600(page: int) -> Path:
    return PAGES_600 / f"page-{page}.png"


# Single illustrations: exclude answer stars, red answer text, adjacent questions,
# and page-divider fragments. Coordinates are from the 150-DPI source renders.
SINGLE_600 = {
    (11, 12): (78, 455, 279, 631),
    (13, 23): (668, 166, 881, 276),
    (13, 29): (687, 1454, 755, 1631),
    (14, 5): (685, 950, 851, 1148),
    (14, 7): (681, 1278, 900, 1485),
    (24, 19): (667, 571, 821, 739),
    (43, 13): (688, 986, 825, 1148),
    (51, 15): (668, 1243, 891, 1449),
    (53, 28): (113, 520, 344, 727),
    (54, 5): (658, 929, 902, 1147),
    (57, 29): (686, 999, 911, 1208),
    (59, 9): (687, 541, 961, 673),
    (61, 29): (667, 946, 763, 1188),
    (63, 9): (685, 144, 945, 371),
    (63, 15): (667, 1175, 812, 1334),
    (65, 29): (686, 1030, 950, 1306),
    (69, 27): (676, 582, 868, 794),
    (69, 28): (83, 620, 378, 917),
    (69, 29): (683, 1137, 976, 1378),
    # The old crop accidentally showed question 28's bend sign.
    (73, 26): (112, 186, 231, 444),
    (75, 10): (62, 122, 283, 365),
    (78, 3): (666, 531, 825, 709),
    (81, 28): (113, 689, 387, 939),
    (81, 29): (714, 1155, 913, 1355),
    (85, 27): (676, 593, 940, 844),
}

for (page, number), box in SINGLE_600.items():
    crop(page_600(page), asset_600(page, number), box)


# Multi-image questions: crop each option independently and redraw neutral 1..4
# labels so the source PDF's red answer marker is never exposed.
STRIPS_600 = {
    (11, 14): [
        (292, 815, 370, 892),
        (175, 812, 252, 892),
        (291, 918, 373, 997),
        (169, 918, 252, 1000),
    ],
    (13, 28): [
        (425, 1028, 531, 1122),
        (174, 1021, 296, 1123),
        (437, 1158, 538, 1255),
        (173, 1158, 296, 1256),
    ],
    (14, 1): [
        (909, 329, 1033, 431),
        (735, 329, 858, 431),
        (909, 454, 1026, 556),
        (734, 454, 860, 557),
    ],
    (21, 30): [
        (397, 1047, 514, 1165),
        (158, 1048, 222, 1165),
        (397, 1182, 514, 1288),
        (158, 1181, 224, 1288),
    ],
    (22, 1): [
        (929, 334, 1067, 423),
        (726, 331, 872, 423),
        (929, 439, 1067, 540),
        (725, 438, 868, 540),
    ],
    (24, 21): [
        (948, 861, 1107, 1027),
        (707, 861, 879, 1028),
        (940, 1049, 1110, 1210),
        (703, 1051, 879, 1210),
    ],
    (27, 14): [
        (309, 1291, 487, 1452),
        (126, 1292, 253, 1452),
        (309, 1454, 450, 1625),
        (126, 1453, 265, 1626),
    ],
    (29, 27): [
        (909, 972, 1033, 1064),
        (727, 971, 850, 1065),
        (907, 1113, 1034, 1209),
        (723, 1112, 834, 1211),
    ],
    (29, 28): [
        (342, 960, 451, 1061),
        (176, 960, 283, 1061),
        (327, 1101, 437, 1204),
        (175, 1101, 256, 1204),
    ],
    (33, 30): [
        (326, 1333, 464, 1423),
        (142, 1332, 281, 1423),
        (329, 1447, 442, 1541),
        (145, 1447, 282, 1542),
    ],
    (43, 15): [
        (922, 1297, 1075, 1456),
        (731, 1297, 870, 1456),
        (921, 1493, 1097, 1649),
        (731, 1493, 871, 1649),
    ],
    (47, 15): [
        (956, 1092, 1084, 1217),
        (765, 1092, 903, 1217),
        (956, 1239, 1087, 1369),
        (764, 1239, 903, 1370),
    ],
    (71, 10): [
        (351, 178, 489, 308),
        (140, 179, 279, 309),
        (347, 331, 486, 459),
        (140, 331, 280, 459),
    ],
    (85, 30): [
        (379, 1015, 535, 1160),
        (187, 1015, 338, 1160),
        (378, 1197, 535, 1346),
        (190, 1198, 339, 1347),
    ],
}

for (page, number), boxes in STRIPS_600.items():
    neutral_strip(page_600(page), asset_600(page, number), boxes)


# The answer star on page 33 overlaps the third sign itself. Replace only that
# tile with the same clean two-way-warning artwork from the duplicate question
# in the first sample PDF; no synthetic sign is drawn.
two_way_source = ASSETS / "q-src-tablo-p041-n034.png"
two_way_destination = asset_600(33, 30)
with Image.open(two_way_source) as source_strip, Image.open(two_way_destination) as destination_strip:
    clean_tile = source_strip.convert("RGB")
    corrected = destination_strip.convert("RGB")
    slot_left = 15 + 2 * 185
    ImageDraw.Draw(corrected).rectangle((slot_left + 1, 3, slot_left + 159, 147), fill="white")
    clean_tile = ImageOps.contain(clean_tile, (158, 143))
    corrected.paste(clean_tile, (slot_left + 1 + (158 - clean_tile.width) // 2, 4))
    corrected.save(two_way_destination, optimize=True)


# Page 28 question 15 is an exact duplicate of a previously prepared neutral
# strip from the other source PDF, so reuse that source-derived asset.
with Image.open(asset_first(28, 5)) as duplicate_strip:
    duplicate_strip.convert("RGB").save(asset_600(28, 15), optimize=True)


# Small fixes in the first source PDF. These crops remain tied to the original
# page and only remove answer text or restore the complete sign boundary.
FIRST_FIXES = {
    (2, 3): (805, 554, 922, 680),
    (2, 4): (135, 550, 252, 683),
    (3, 24): (116, 965, 418, 1072),
    (4, 5): (795, 785, 935, 879),
    (8, 2): (120, 440, 235, 580),
    (10, 1): (790, 435, 940, 526),
    (10, 2): (120, 435, 260, 516),
    (10, 4): (120, 570, 255, 654),
    (26, 6): (122, 712, 210, 804),
    (28, 10): (120, 990, 232, 1100),
    (30, 11): (804, 1264, 912, 1358),
}

for (page, number), box in FIRST_FIXES.items():
    crop(PAGES_FIRST / f"page-{page}.png", asset_first(page, number), box)


# Rebuild page 2 question 1 without the red option label printed under the
# correct source choice or the neighboring question text.
neutral_strip(
    PAGES_FIRST / "page-2.png",
    asset_first(2, 1),
    [
        (1172, 397, 1271, 489),
        (1064, 397, 1161, 489),
        (950, 397, 1043, 489),
        (823, 397, 916, 489),
    ],
)


# Two assets from tablo.pdf previously included answer text to the right of the
# sign. Keep only the actual sign from the original 150-DPI page renders.
crop(
    PAGES_TABLO / "page-56.png",
    ASSETS / "q-src-tablo-p056-n088.png",
    (14, 513, 394, 896),
)
crop(
    PAGES_TABLO / "page-83.png",
    ASSETS / "q-src-tablo-p083-n183.png",
    (13, 1305, 393, 1693),
)


# Tighten three photographed pages from ایین نامه-1.pdf to the actual visual
# stimulus. The previous crops included the printed answer line or heading.
crop(
    PAGES_AYIN / "page-14.png",
    ASSETS / "q-src-ayin1-e05-p14-n05.png",
    (600, 1090, 735, 1210),
)
crop(
    PAGES_AYIN / "page-17.png",
    ASSETS / "q-src-ayin1-e06-p17-n28.png",
    (1138, 808, 1268, 935),
)
crop(
    PAGES_AYIN / "page-21.png",
    ASSETS / "q-src-ayin1-e07-p21-n07.png",
    (1590, 130, 1685, 220),
)


print(
    f"fixed {len(SINGLE_600) + len(STRIPS_600) + 7 + len(FIRST_FIXES)} "
    "referenced question assets"
)
