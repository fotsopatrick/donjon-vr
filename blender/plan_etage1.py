# Plan ETAGE 1 — chateau concentrique reel (28 large x 18 haut)
# Entree en bas -> outer bailey (anneau) -> inner gatehouse (haut) -> keep central (cle+boss) -> sortie
W,H = 28,18
g = [['#']*W for _ in range(H)]
def rect(x0,y0,x1,y1,ch='.'):
    for y in range(y0,y1+1):
        for x in range(x0,x1+1):
            g[y][x]=ch
# --- outer bailey : anneau large juste dans les murs exterieurs ---
rect(2,2,25,15)            # cour interieure creusee
# --- mur interieur (enceinte du keep) : on re-mure un rectangle central ---
for y in range(5,13):
    for x in range(9,19):
        g[y][x]='#'
rect(10,6,17,11)           # inner bailey (dans l'enceinte interieure)
# --- keep central : petite salle forte ---
for y in range(7,11):
    for x in range(12,16):
        g[y][x]='#'
rect(13,8,14,9)            # coeur du keep (creux)
# --- gatehouses (passages controles) ---
g[15][13]='.'; g[15][14]='.'   # entree principale (bas)
g[16][13]='S'; g[16][14]='.'   # spawn juste derriere l'entree
g[5][13]='.'; g[5][14]='.'     # inner gatehouse (haut) -> il faut faire le tour
g[6][13]='.'; g[6][14]='.'
g[11][13]='.'; g[11][14]='.'   # porte du keep (bas du keep)
g[10][13]='.'; g[10][14]='.'
# --- cle au coeur du keep, boss devant, sortie a l'arriere ---
g[8][13]='K'                   # la cle, gardee au centre
g[9][14]='B'                   # le boss dans le keep
g[2][13]='D'                   # la sortie (escalier) tout au fond, au nord
# --- tours d'angle (drum towers) : 4 coins, tresors et gardes ---
for (cx,cy,mk) in [(4,4,'C'),(23,4,'E'),(4,13,'E'),(23,13,'C')]:
    rect(cx-1,cy-1,cx+1,cy+1)
    g[cy][cx]=mk
# --- verif taille + connexite (entree -> cle -> sortie) ---
rows=[''.join(r) for r in g]
assert len(rows)==H and all(len(r)==W for r in rows), "TAILLE KO"
from collections import deque
def bfs(sy,sx):
    seen=set([(sy,sx)]); q=deque([(sy,sx)])
    while q:
        y,x=q.popleft()
        for dy,dx in((1,0),(-1,0),(0,1),(0,-1)):
            ny,nx=y+dy,x+dx
            if 0<=ny<H and 0<=nx<W and (ny,nx) not in seen and g[ny][nx]!='#':
                seen.add((ny,nx)); q.append((ny,nx))
    return seen
def find(ch):
    for y in range(H):
        for x in range(W):
            if g[y][x]==ch: return (y,x)
Sy,Sx=find('S'); acc=bfs(Sy,Sx)
print('\n'.join(rows))
print('---')
print('taille 28x18 :', 'OK')
print('entree -> cle  :', 'OK' if find('K') in acc else 'BLOQUE')
print('entree -> sortie:', 'OK' if find('D') in acc else 'BLOQUE')
print('entree -> boss :', 'OK' if find('B') in acc else 'BLOQUE')
