#!/usr/bin/env python3
"""Dessine l'étage 2 du donjon — « les cryptes » — au format de tuiles
que lisent le poseur (donjon-plan.html) et le jeu (PLAN lignes).
Vérifie le contrôle du poseur : clé, boss et sortie atteignables
depuis l'entrée (BFS, cases bloquantes # e l v T)."""
from collections import deque

W, H = 28, 18
g = [['#'] * W for _ in range(H)]


def salle(x1, z1, x2, z2, sol='.'):
    for y in range(z1, z2 + 1):
        for x in range(x1, x2 + 1):
            g[y][x] = sol


def porte(x, y):
    g[y][x] = '.'


# ── les salles ──────────────────────────────────────────────────────────
salle(1, 1, 8, 5)          # salle d'entrée
salle(12, 1, 26, 7)        # la grande salle des gardes
salle(10, 10, 16, 16)      # la salle de la clé
salle(18, 9, 26, 16)       # la crypte du boss
for x in (9, 10, 11):      # entrée → grande salle (couloir)
    porte(x, 3)
for y in range(8, 10):     # fin du couloir qui descend
    porte(13, y)
porte(17, 12)              # salle de la clé → crypte du boss

# ── les objets ──────────────────────────────────────────────────────────
g[2][2] = 'S'              # l'entrée du joueur
g[1][6] = 'F'; g[5][1] = 'F'
g[2][15] = 'E'; g[6][20] = 'E'; g[1][24] = 'E'; g[6][16] = 'E'
g[2][25] = 'C'; g[6][13] = 'C'
g[13][13] = 'K'            # la clé, au fond de sa salle
g[12][11] = 'E'; g[15][15] = 'E'   # ses gardes
g[12][22] = 'B'            # le boss
g[10][20] = 'C'; g[15][24] = 'C'; g[15][19] = 'C'
g[9][25] = 'F'; g[16][19] = 'F'
g[14][25] = 'V'            # l'escalier qui descend vers l'étage 3
g[10][18] = 'M'            # l'escalier qui remonte à l'étage 1
g[16][13] = 'D'            # la sortie

lignes = [''.join(r) for r in g]

# ── le contrôle du poseur ───────────────────────────────────────────────
BLOQUE = set('#elvT')
depart = next((x, y) for y in range(H) for x in range(W) if g[y][x] == 'S')
vus = {depart}
file = deque([depart])
while file:
    x, y = file.popleft()
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in vus and g[ny][nx] not in BLOQUE:
            vus.add((nx, ny)); file.append((nx, ny))
for nom, ch in (("la clé", 'K'), ("le boss", 'B'), ("la sortie", 'D'),
                ("l'escalier qui descend", 'V')):
    pos = [(x, y) for y in range(H) for x in range(W) if g[y][x] == ch]
    ok = bool(pos) and pos[0] in vus
    print(("✓" if ok else "✗"), nom, "atteignable" if ok else "BLOQUÉ")

# ── la sortie ───────────────────────────────────────────────────────────
import json, os
ICI = os.path.dirname(os.path.abspath(__file__))
sol, obj = [], []
OBJETS = set('SDMVPKCBENHAF')
for r in lignes:
    sol.append(''.join('.' if c in OBJETS else c for c in r))
    obj.append(''.join(c if c in OBJETS else '-' for c in r))
carte = {"nom": "etage2-cryptes", "largeur": W, "hauteur": H,
         "legende_sol": {"#": "Mur", ".": "Sol nu"},
         "legende_objets": {"S": "Entrée", "D": "Sortie", "M": "Escalier qui monte",
                            "V": "Escalier qui descend", "K": "Clé", "C": "Coffre",
                            "B": "Boss", "E": "Ennemi", "F": "Torche"},
         "bloquants": ["#", "e", "l", "v", "T"],
         "sol": sol, "objets": obj}
with open(os.path.join(ICI, "etage2-cryptes.json"), "w") as f:
    json.dump(carte, f, ensure_ascii=False, indent=1)
with open(os.path.join(ICI, "etage2-cryptes-lignes.txt"), "w") as f:
    f.write("\n".join(lignes) + "\n")
print("\n".join(lignes))
print(f"→ {ICI}/etage2-cryptes.json")
