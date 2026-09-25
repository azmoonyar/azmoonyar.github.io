#!/usr/bin/env python3
"""Crop visual stimuli for exam 8. No OCR is performed."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];SOURCE=Path('/private/tmp/ayeenname-ayin1-exam8');OUTPUT=ROOT/'assets'/'questions'
CROPS={2:(23,80,500,300,720),3:(23,650,900,900,1120),4:(23,75,900,290,1130),5:(23,750,1360,950,1600),7:(24,1950,120,2150,350),22:(24,75,1370,370,1630),23:(23,1950,140,2220,410),27:(23,1850,930,2040,1220),28:(23,1380,930,1660,1220)}
COMPOSITES={
1:(23,[(1010,540,1170,715),(750,540,800,715),(1010,720,1170,900),(750,720,900,900)]),
6:(23,[(410,1430,570,1580),(145,1430,305,1580),(410,1580,570,1740),(145,1580,305,1740)]),
30:(23,[(1640,1430,1800,1580),(1390,1430,1550,1580),(1640,1580,1800,1740),(1390,1580,1550,1740)]),
}
def composite(source,boxes):
 canvas=Image.new('RGB',(500,390),'white');draw=ImageDraw.Draw(canvas);fp=Path('/System/Library/Fonts/Supplemental/Arial.ttf');font=ImageFont.truetype(str(fp),28) if fp.exists() else ImageFont.load_default();pos=[(275,15),(15,15),(275,205),(15,205)]
 for n,(box,(x,y)) in enumerate(zip(boxes,pos),1):
  im=source.crop(box);im.thumbnail((175,160));canvas.paste(im,(x+(175-im.width)//2,y+18+(160-im.height)//2));draw.text((x+195,y+78),str(n),fill='black',font=font)
 return canvas
OUTPUT.mkdir(parents=True,exist_ok=True)
for n,(p,boxes) in COMPOSITES.items():
 im=Image.open(SOURCE/f'page-{p}.png').convert('RGB');composite(im,boxes).save(OUTPUT/f'q-src-ayin1-e08-p{p}-n{n:02}.png',optimize=True)
for n,(p,l,t,r,b) in CROPS.items():
 Image.open(SOURCE/f'page-{p}.png').convert('RGB').crop((l,t,r,b)).save(OUTPUT/f'q-src-ayin1-e08-p{p}-n{n:02}.png',optimize=True)
print(f'saved {len(CROPS)+len(COMPOSITES)} crops')
