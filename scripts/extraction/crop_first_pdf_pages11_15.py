from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tmp" / "pdfs" / "first-pdf-pages-11-16"
OUTPUT = ROOT / "assets" / "questions"
BOXES = {
    (11, 15): (770, 175, 1050, 280),
    (13, 25): (790, 920, 950, 1080),
    (15, 15): (780, 145, 970, 310),
}


for (page, number), box in BOXES.items():
    with Image.open(SOURCE / f"page-{page:02d}.png") as image:
        destination = OUTPUT / f"q-src-4-5888983329180487891-1-p{page:03d}-n{number:02d}.png"
        image.convert("RGB").crop(box).save(destination, optimize=True)

print(f"saved {len(BOXES)} question assets")
