#!/usr/bin/env python3
"""Crop visual stimuli for exam 3 without OCR."""
from pathlib import Path
from PIL import Image
from crop_ayin1_exam1 import remove_green_answer_marks, trim_white

ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path("/private/tmp/ayeenname-ayin1-hi")
OUTPUT=ROOT/"assets"/"questions"
CROPS={
1:(8,500,345,930,720),2:(8,55,345,470,720),3:(8,510,700,700,970),
4:(8,55,700,285,980),5:(8,505,1060,700,1320),6:(8,50,1050,280,1320),
7:(9,1510,70,1910,260),8:(9,1040,70,1430,280),
23:(8,1550,100,1880,300),28:(8,1160,850,1515,1100),29:(8,1530,1040,1645,1330),
}
NO_MASK={23,29}
MANUAL_PATCHES={28:(0,150,45,250)}
OUTPUT.mkdir(parents=True,exist_ok=True)
for n,(p,l,t,r,b) in CROPS.items():
    crop=Image.open(SOURCE/f"page-{p:02}.png").convert("RGB").crop((l,t,r,b))
    if n not in NO_MASK: crop=remove_green_answer_marks(crop)
    if n in MANUAL_PATCHES:
        x0,y0,x1,y1=MANUAL_PATCHES[n]
        crop.paste((225,222,157),(x0,y0,x1,y1))
    crop=trim_white(crop)
    crop.save(OUTPUT/f"q-src-ayin1-e03-p{p:02}-n{n:02}.png",optimize=True)
print(f"saved {len(CROPS)} crops")
