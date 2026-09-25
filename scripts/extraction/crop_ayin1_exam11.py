#!/usr/bin/env python3
"""Crop visual stimuli for exam 11. No OCR is performed."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];SOURCE=Path('/private/tmp/ayeenname-ayin1-exam11');OUTPUT=ROOT/'assets'/'questions'
CROPS={2:(32,90,430,320,680),3:(32,700,900,930,1140),4:(32,80,900,330,1150),5:(32,700,1340,920,1590),6:(32,70,1340,320,1590),7:(33,1940,100,2260,390),8:(33,1410,120,1550,345),12:(33,1400,950,1710,1260),23:(32,1960,90,2225,385),25:(32,1960,550,2230,850),28:(32,1390,930,1625,1200),29:(32,1980,1320,2180,1600)}
COMPOSITES={1:(32,[(1000,480,1175,690),(735,480,910,690),(1000,690,1175,900),(735,690,910,900)]),24:(32,[(1640,130,1810,340),(1390,130,1570,340),(1640,340,1810,520),(1390,340,1570,520)])}
def composite(source,boxes):
 canvas=Image.new('RGB',(500,390),'white');draw=ImageDraw.Draw(canvas);fp=Path('/System/Library/Fonts/Supplemental/Arial.ttf');font=ImageFont.truetype(str(fp),28) if fp.exists() else ImageFont.load_default();pos=[(275,15),(15,15),(275,205),(15,205)]
 for n,(box,(x,y)) in enumerate(zip(boxes,pos),1):
  im=source.crop(box);im.thumbnail((175,160));canvas.paste(im,(x+(175-im.width)//2,y+18+(160-im.height)//2));draw.text((x+195,y+78),str(n),fill='black',font=font)
 return canvas
OUTPUT.mkdir(parents=True,exist_ok=True)
for n,(p,boxes) in COMPOSITES.items():
 im=Image.open(SOURCE/f'page-{p}.png').convert('RGB');composite(im,boxes).save(OUTPUT/f'q-src-ayin1-e11-p{p}-n{n:02}.png',optimize=True)
for n,(p,l,t,r,b) in CROPS.items():
 Image.open(SOURCE/f'page-{p}.png').convert('RGB').crop((l,t,r,b)).save(OUTPUT/f'q-src-ayin1-e11-p{p}-n{n:02}.png',optimize=True)
print(f'saved {len(CROPS)+len(COMPOSITES)} crops')
