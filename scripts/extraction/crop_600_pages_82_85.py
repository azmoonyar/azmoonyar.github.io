from pathlib import Path
from PIL import Image

SOURCE=Path("/private/tmp/ayeenname-600-driveing-81-85"); OUTPUT=Path("assets/questions")
CROPS={(82,5):(535,630,800,850),(83,10):(60,115,280,340),(83,12):(55,385,190,650),(83,14):(535,690,735,900),(83,15):(545,1000,700,1190),(83,16):(75,995,300,1200),(84,23):(540,1000,700,1180),(84,24):(65,980,485,1110),(85,25):(535,130,745,365),(85,26):(70,105,285,365),(85,27):(535,415,785,665),(85,28):(65,405,290,650),(85,29):(545,805,775,1055),(85,30):(90,775,440,1115)}
OUTPUT.mkdir(parents=True,exist_ok=True)
for (page,number),box in CROPS.items():
    with Image.open(SOURCE/f"page-{page}.png") as image:
        image.crop(box).save(OUTPUT/f"q-src-600-driveing-p{page:03d}-n{number:02d}.png",optimize=True)
