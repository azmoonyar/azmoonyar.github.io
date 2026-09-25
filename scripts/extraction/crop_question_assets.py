"""Create question-only image crops from visually reviewed PDF renders.

No OCR is used. Coordinates are recorded only after manual visual inspection.
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("/private/tmp/ayeenname-pdf-pages/test-03.png")
OUTPUT = ROOT / "assets" / "questions"

# (filename, left, top, right, bottom) in the 1489x2105 visual render.
CROPS = [
    # Extra margin preserves the full left and right carriageway sections.
    ("q-src-4-5888983329180487891-1-p003-n23.png", 724, 862, 1062, 1052),
    ("q-src-4-5888983329180487891-1-p003-n24.png", 116, 965, 418, 1098),
    ("q-src-4-5888983329180487891-1-p003-n29.png", 782, 1618, 944, 1704),
]


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    image = Image.open(SOURCE)
    for filename, left, top, right, bottom in CROPS:
        image.crop((left, top, right, bottom)).save(OUTPUT / filename, "PNG")


if __name__ == "__main__":
    main()
