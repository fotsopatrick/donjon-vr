#!/usr/bin/env python3
"""P3.1b - rend la photo du mur reellement tileable.

Methode : on roule l'image d'une demi-taille (la mauvaise couture vient
au centre), puis on fond doucement (smoothstep) vers ce roulement sur
tout le reste : pres des bords, c'est le roulement (continu a travers
la reprise) qui gagne ; dans la bande centrale, c'est l'original
(continu la). Meme photo, meme pierres, meme contraste.
"""
import numpy as np
from PIL import Image

SRC = "/home/orel/donjon-vr/assets/textures/mur-pierre.jpg"
DST = "/home/orel/donjon-vr/assets/textures/mur-pierre-tileable.jpg"
FEATHER = 150   # largeur du fondu autour de la couture centrale


def smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def couture(img):
    """Ecart moyen entre premier et dernier rang / colonne."""
    g = img.astype(np.float32)
    dx = np.abs(g[:, 0, :] - g[:, -1, :]).mean()
    dy = np.abs(g[0, :, :] - g[-1, :, :]).mean()
    return float(dx), float(dy)


def soude(img, axe):
    """Ressout une axe : roule d'une demi-taille puis fond au centre."""
    ax = 1 if axe == "x" else 0
    n = img.shape[ax]
    r = np.roll(img, n // 2, axis=ax)
    coords = (np.arange(n) + 0.5) - n / 2.0
    if axe == "y":
        dist = np.abs(coords)[:, None]
    else:
        dist = np.abs(coords)[None, :]
    poids_roule = smoothstep(dist / FEATHER)   # 0 au centre, 1 aux bords
    alpha = poids_roule[..., None]
    return alpha * r + (1.0 - alpha) * img


img = Image.open(SRC).convert("RGB")
base = np.asarray(img).astype(np.float32)

avant = couture(base)

base = soude(base, "x")   # soude la reprise verticale (gauche/droite)
base = soude(base, "y")   # soude la reprise horizontale (haut/bas)

apres = couture(base)

Image.fromarray(base.clip(0, 255).astype(np.uint8)).save(DST, quality=93)
print(f"ecart bord vertical  : {avant[0]:6.2f} -> {apres[0]:6.2f}")
print(f"ecart bord horizontal: {avant[1]:6.2f} -> {apres[1]:6.2f}")
print("ecrit :", DST)
