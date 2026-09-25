from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets" / "questions"
OUTPUT = ROOT / "tmp" / "pdfs" / "asset-qa"
OUTPUT.mkdir(parents=True, exist_ok=True)


def referenced_asset_names() -> set[str]:
    script = """
import path from 'node:path';
import { mockQuestions } from './questions.js';
const names = [...new Set(mockQuestions.filter(q => q.image?.src).map(q => path.basename(q.image.src)))];
process.stdout.write(names.join('\\n'));
"""
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {line for line in result.stdout.splitlines() if line}


def edge_red_score(path: Path) -> tuple[float, float]:
    with Image.open(path) as source:
        image = source.convert("RGB")
    width, height = image.size
    margin = max(3, min(width, height) // 12)
    red = yellow = edge = 0
    for y in range(height):
        for x in range(width):
            if not (x < margin or x >= width - margin or y < margin or y >= height - margin):
                continue
            edge += 1
            r, g, b = image.getpixel((x, y))
            if r > 165 and r > g * 1.45 and r > b * 1.35:
                red += 1
            if r > 190 and g > 175 and b < 160:
                yellow += 1
    return red / edge, yellow / edge


referenced = referenced_asset_names()
ranked = []
for asset in ASSETS.glob("*.png"):
    if asset.name not in referenced:
        continue
    red_ratio, yellow_ratio = edge_red_score(asset)
    if red_ratio >= 0.008:
        ranked.append((yellow_ratio > 0.2, red_ratio, asset))

ranked.sort(reverse=True, key=lambda item: (item[0], item[1]))
selected = [item[2] for item in ranked[:80]]

font = ImageFont.load_default()
for sheet_number, start in enumerate(range(0, len(selected), 16), start=1):
    canvas = Image.new("RGB", (1200, 920), "#eef1f6")
    draw = ImageDraw.Draw(canvas)
    for position, path in enumerate(selected[start:start + 16]):
        row, column = divmod(position, 4)
        left = column * 300 + 10
        top = row * 230 + 10
        with Image.open(path) as source:
            tile = ImageOps.contain(source.convert("RGB"), (270, 180))
        canvas.paste(tile, (left + (270 - tile.width) // 2, top))
        draw.rectangle((left, top, left + 280, top + 215), outline="#bbc2ce", width=2)
        label = path.stem.replace("q-src-", "")
        draw.text((left + 8, top + 190), label[:43], fill="#111827", font=font)
    canvas.save(OUTPUT / f"suspicious-edge-red-{sheet_number:02d}.png", optimize=True)

print(
    f"created {sheet_number} sheets for {len(selected)} suspicious assets "
    f"from {len(referenced)} referenced PNGs"
)
