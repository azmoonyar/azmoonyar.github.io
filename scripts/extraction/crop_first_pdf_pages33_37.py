from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
PAGES = ROOT / "tmp" / "pdfs" / "first-pdf-pages-33-37"
OUT = ROOT / "assets" / "questions"
OUT.mkdir(parents=True, exist_ok=True)


def crop(page: int, number: int, box: tuple[int, int, int, int]) -> None:
    source_path = PAGES / f"page-{page}.png"
    output_path = OUT / f"q-src-4-5888983329180487891-1-p{page:03d}-n{number:02d}.png"
    with Image.open(source_path) as source:
        source.crop(box).save(output_path, optimize=True)


# Only the illustration belonging to each question is retained; the red source
# answer text is deliberately outside every crop.
crop(33, 15, (616, 524, 834, 696))
crop(33, 17, (624, 882, 806, 1068))
crop(34, 27, (622, 636, 850, 810))
crop(34, 29, (646, 874, 850, 988))
crop(34, 30, (78, 854, 334, 940))
crop(35, 12, (78, 1380, 208, 1528))
crop(36, 14, (80, 106, 384, 182))
crop(36, 15, (632, 318, 866, 388))
crop(36, 18, (110, 614, 210, 710))
crop(37, 26, (80, 132, 388, 308))
crop(37, 30, (100, 578, 230, 686))
