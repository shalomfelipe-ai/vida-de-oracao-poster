# -*- coding: utf-8 -*-
import os,sys
D=os.path.dirname(os.path.abspath(__file__)); B=os.path.dirname(D)
sys.path.insert(0,os.path.join(B,"piloto-visual","templates"))
from templates import *
from PIL import Image, ImageDraw
CR,MU,GO=CREAM,CREAM_D,GOLD
M=Image.open(f"{D}/murillo_inmaculada_venerables_pd.jpg").convert("RGB")
def framed(img,w,h):
    im=img.resize((w,h),Image.LANCZOS); fr=Image.new("RGB",(w+24,h+24),GOLD_S)
    fr.paste(Image.new("RGB",(w+12,h+12),BROWN_D),(6,6)); fr.paste(im,(12,12)); return fr
h=700; w=int(M.width*h/M.height); bg=grad_bg(1080,1350); fr=framed(M,w,h); bg.paste(fr,((1080-fr.width)//2,56)); bg.save(f"{D}/_bg_im.png")
feed_card(f"{D}/_bg_im.png","IMACULADA CONCEIÇÃO",
  [("A graça chegou",56,False,CR),("antes do",44,True,MU),("pedido",92,False,GO)],
  sub=["Maria foi preparada antes de saber que seria preciso.","A oração também começa antes de você."],
  cta="arraste  ›",band="base",color=1.0,bright=1.0,mult=0.0,strength=120,vig=0.25).save(f"{D}/d08_capa.png")
feed_card(f"{D}/_bg_im.png","IMACULADA CONCEIÇÃO",
  [("Salva antes",56,False,CR),("de cair",92,False,GO),("cheia de graça",44,True,MU)],
  sub=["Ela foi preservada do pecado desde o começo.","Manda pra quem tem devoção a ela."],
  cta=None,band="base",color=1.0,bright=1.0,mult=0.0,strength=120,vig=0.25).save(f"{D}/d08_santo.png")
W,H=1080,1920; cv=grad_bg(W,H); w=620; h=int(M.height*w/M.width); fr=framed(M,w,h); cv.paste(fr,((W-fr.width)//2,600)); d=ImageDraw.Draw(cv)
kicker(d,W,170,"IMACULADA CONCEIÇÃO",col=GOLD,st=1)
t="Cheia de graça"; ts=fit(d,t,80,W-200,600); ctext(d,W,250,t,lora(ts,600),CR,st=2)
yb=360
for ln in wrap(d,"A saudação do anjo a chama de cheia de graça. Maria já estava cheia antes de ouvir o pedido.",lora(40,400,italic=True),W-200):
    ctext(d,W,yb,ln,lora(40,400,italic=True),SAND,st=2); yb+=56
fh=lora(34,500); hint="O que você diria a Maria hoje?"; hl=wrap(d,hint,fh,W-320); bh=44+len(hl)*46; hy=H-250
d.rounded_rectangle([140,hy,W-140,hy+bh],radius=26,outline=GOLD,width=2); yy=hy+22
for ln in hl: ctext(d,W,yy,ln,fh,CR,st=1); yy+=46
footer(d,W,H,cta=None); cv.save(f"{D}/d08_santo_story.png")
ims=[Image.open(f"{D}/{n}") for n in ("d08_capa.png","d08_santo.png","d08_santo_story.png")]
ims=[i.resize((int(i.width*800/i.height),800)) for i in ims]
s=Image.new("RGB",(sum(i.width for i in ims)+40,800),(15,15,15)); x=0
for i in ims: s.paste(i,(x,0)); x+=i.width+20
s.save(f"{D}/previa_imaculada.png"); print("ok")
