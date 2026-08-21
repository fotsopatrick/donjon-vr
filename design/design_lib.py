# -*- coding: utf-8 -*-
"""
design_lib — donner des « yeux » chiffrés au design de KOTOAGE.

Décode un PNG (Python pur, zlib) puis mesure la palette d'une image de jeu et la
COMPARE au goût de Patrick (cf. mémoire gout-arene-cyberpunk / gout-assets-3d) :
cyberpunk néon nocturne OUI, plaine verte NON.

Deux algorithmes de comparaison réutilisables :
  1) score_palettes()  : à quelle « famille de goût » l'image ressemble le plus
                         (cyberpunk vs plaine verte), par couverture de couleurs-repères.
  2) distance_hist()   : distance entre DEUX images (intersection d'histogrammes),
                         0 = identiques, 1 = tout oppose. Sert à dire « l'arène est
                         plus proche du cyberpunk de référence que de la plaine ».
"""
import zlib, struct

# ---------- décodage PNG minimal (couleurs 2=RGB / 6=RGBA, 8 bits, non entrelacé) ----------
def _paeth(a,b,c):
    p=a+b-c; pa=abs(p-a); pb=abs(p-b); pc=abs(p-c)
    if pa<=pb and pa<=pc: return a
    if pb<=pc: return b
    return c

def decode_png(chemin):
    d=open(chemin,'rb').read()
    assert d[:8]==b'\x89PNG\r\n\x1a\n', "pas un PNG"
    i=8; w=h=bit=ct=None; idat=bytearray()
    while i<len(d):
        ln=struct.unpack('>I',d[i:i+4])[0]; typ=d[i+4:i+8]; data=d[i+8:i+8+ln]; i+=12+ln
        if typ==b'IHDR':
            w,h,bit,ct=struct.unpack('>IIBB',data[:10])
        elif typ==b'IDAT': idat+=data
        elif typ==b'IEND': break
    assert bit==8 and ct in (2,6), "format PNG non gere (bit=%s ct=%s)"%(bit,ct)
    ch=3 if ct==2 else 4
    raw=zlib.decompress(bytes(idat))
    stride=w*ch
    out=bytearray(stride*h); prev=bytearray(stride)
    pos=0
    for y in range(h):
        f=raw[pos]; pos+=1
        line=bytearray(raw[pos:pos+stride]); pos+=stride
        if f==1:
            for x in range(ch,stride): line[x]=(line[x]+line[x-ch])&255
        elif f==2:
            for x in range(stride): line[x]=(line[x]+prev[x])&255
        elif f==3:
            for x in range(stride):
                a=line[x-ch] if x>=ch else 0
                line[x]=(line[x]+((a+prev[x])>>1))&255
        elif f==4:
            for x in range(stride):
                a=line[x-ch] if x>=ch else 0
                c=prev[x-ch] if x>=ch else 0
                line[x]=(line[x]+_paeth(a,prev[x],c))&255
        out[y*stride:(y+1)*stride]=line; prev=line
    return w,h,ch,out

def pixels(chemin, pas=4):
    """Rend une liste (r,g,b) sous-échantillonnée (1 pixel sur `pas` en x et y)."""
    w,h,ch,buf=decode_png(chemin); res=[]
    stride=w*ch
    for y in range(0,h,pas):
        base=y*stride
        for x in range(0,w,pas):
            o=base+x*ch; res.append((buf[o],buf[o+1],buf[o+2]))
    return res

# ---------- classification d'un pixel par « famille » ----------
def lum(r,g,b): return 0.299*r+0.587*g+0.114*b

def famille(r,g,b):
    L=lum(r,g,b)
    if L<40: return 'sombre'                                  # fond nuit
    if g>130 and b>130 and r<120: return 'cyan'              # néon cyan
    if r>120 and b>110 and g<110: return 'magenta'          # néon magenta
    if r>150 and g>115 and b<120 and g>=b: return 'ambre'   # fenêtre chaude
    if g>=r and g>=b and g>90 and g>r*1.12 and g>b*1.12: return 'vert'   # herbe
    if b>150 and g>140 and r>115 and L>150: return 'ciel_pale'          # ciel bleu clair
    return 'autre'

def profil(px):
    """Fractions par famille + luminance moyenne."""
    n=len(px); c={}
    Ls=0.0
    for r,g,b in px:
        f=famille(r,g,b); c[f]=c.get(f,0)+1; Ls+=lum(r,g,b)
    return {k:v/n for k,v in c.items()}, Ls/n

# ---------- ALGO 1 : à quelle famille de goût l'image ressemble ----------
# poids : le néon compte fort (rare mais signant), le sombre soutient le cyberpunk.
def score_palettes(px):
    fr,L=profil(px)
    g=lambda k:fr.get(k,0.0)
    s_cyber  = g('sombre')*1.0 + g('cyan')*6 + g('magenta')*6 + g('ambre')*1.5
    s_plaine = g('vert')*6 + g('ciel_pale')*4 + max(0,(L-120)/135)*1.0
    verdict = 'cyberpunk' if s_cyber>s_plaine else 'plaine_verte'
    return {'cyberpunk':round(s_cyber,4),'plaine_verte':round(s_plaine,4),
            'verdict':verdict,'fractions':{k:round(v,4) for k,v in fr.items()},
            'luminance':round(L,1)}

# ---------- ALGO 2 : distance entre deux images (intersection d'histogrammes) ----------
def _hist(px, bits=3):
    sh=8-bits; nb=1<<bits; H=[0]*(nb*nb*nb)
    for r,g,b in px:
        H[((r>>sh)<<(2*bits))|((g>>sh)<<bits)|(b>>sh)]+=1
    t=sum(H) or 1
    return [v/t for v in H]

def distance_hist(pxA, pxB, bits=3):
    a=_hist(pxA,bits); b=_hist(pxB,bits)
    inter=sum(min(x,y) for x,y in zip(a,b))
    return round(1.0-inter,4)   # 0 = identiques, 1 = disjointes
