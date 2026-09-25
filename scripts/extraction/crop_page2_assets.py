"""Crops recorded from a direct visual inspection of source PDF page 2."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tmp" / "pdfs" / "first-page2-audit" / "page-02-180.png"
OUTPUT = ROOT / "assets" / "questions"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    image = Image.open(SOURCE)
    crops = [
        ("q-src-4-5888983329180487891-1-p002-n01.png", (814, 392, 1336, 518)),
        ("q-src-4-5888983329180487891-1-p002-n02.png", (112, 360, 269, 505)),
        ("q-src-4-5888983329180487891-1-p002-n03.png", (805, 554, 967, 680)),
        ("q-src-4-5888983329180487891-1-p002-n04.png", (135, 550, 310, 683)),
        ("q-src-4-5888983329180487891-1-p002-n05.png", (797, 699, 1040, 865)),
        ("q-src-4-5888983329180487891-1-p002-n06.png", (220, 730, 760, 840)),
        ("q-src-4-5888983329180487891-1-p002-n07.png", (805, 900, 1003, 1047)),
        ("q-src-4-5888983329180487891-1-p002-n09.png", (790, 1145, 874, 1255)),
        ("q-src-4-5888983329180487891-1-p002-n14.png", (110, 1605, 245, 1682)),
        ("q-src-4-5888983329180487891-1-p002-n11.png", (794, 1415, 1094, 1593)),
    ]
    for filename, rectangle in crops:
        image.crop(rectangle).save(OUTPUT / filename, "PNG")


if __name__ == "__main__":
    main()
