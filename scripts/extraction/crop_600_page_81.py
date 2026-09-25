from pathlib import Path
from PIL import Image

source = Path("/private/tmp/ayeenname-600-driveing-81-85/page-81.png")
output = Path("assets/questions")
crops = {25:(545,95,710,285),26:(65,90,310,350),27:(535,390,770,665),28:(70,390,325,675),29:(550,820,770,1065)}
output.mkdir(parents=True, exist_ok=True)
with Image.open(source) as image:
    for number, box in crops.items():
        image.crop(box).save(output / f"q-src-600-driveing-p081-n{number:02d}.png", optimize=True)
