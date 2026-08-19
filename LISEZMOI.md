# KOTOAGE — le donjon où l'on prononce

*(Le jeu s'appelait « Le Petit Donjon » en 2D. Kotoage — 言挙げ — veut dire
« élever le mot » : déclarer son intention à voix haute pour qu'elle agisse.)*

Version 3D à la première et à la troisième personne du jeu
`~/tour/jeux/donjon/index.html` (rapatrié du VPS le 18/08/2026). **Le jeu
d'origine n'a pas été touché et reste hors ligne, comme voulu.**

## Lancer

Double-clic sur **Le Petit Donjon** sur le Bureau, ou :

    cd ~/donjon-vr && python3 -m http.server 8099 --bind 127.0.0.1

puis `http://127.0.0.1:8099/index.html` dans un onglet Chrome **normal**.
(Le petit serveur est obligatoire : les navigateurs refusent de charger des
modèles 3D depuis un fichier ouvert en double-clic. Ce n'est pas un choix.)

Trois pages :

| Page | Ce que c'est |
|---|---|
| `index.html` | le jeu |
| `demo-realiste.html` | essai d'ambiance photoréaliste (ciel HDRI + rochers scannés) |
| `demo-splat.html` | essai de scène capturée en photos (Gaussian Splatting) |

## Les commandes

| Touche | Effet |
|---|---|
| Z Q S D | marcher |
| souris | regarder (clic pour capturer, ou maintenir et tirer) |
| ← → ↑ ↓ | tourner et lever le regard, sans souris |
| Maj | courir |
| Espace | foncer (invulnérable pendant l'élan) |
| clic gauche | frapper — enchaînement à 4 temps |
| **V maintenu** | **parler à l'esprit du donjon** |
| C | lui écrire |
| E ou Tab | la fenêtre de statut |
| F | se voir en entier (3e personne) |
| P | baisser d'un cran de qualité |
| Maj+C | ciel photographié / ciel peint |

Manette Xbox reconnue (sticks, A frapper, B foncer, X parler, Y statut) —
**en filaire uniquement**, cette machine n'a aucun Bluetooth.

## Ce qu'il y a dedans

**Le hameau (étage 0)** — douze maisons à colombages, deux rues pavées qui se
croisent, une place ronde avec un puits, une palissade, une forêt, un ciel
photographié avec des montagnes à l'horizon. On y apparaît ; l'escalier
descend au donjon, au sud.

**Cinq étages**, chacun sa faune et sa teinte : les caves (slimes, bleu),
l'ossuaire (paysans squelettes, violet), les galeries (rats, vert), le voile
(spectres qui traversent les murs, rose), le palier (rouge).

**Un gardien tous les cinq étages.** Il dort, il charge, il écrase le sol en
lançant une onde, il crache des rejetons, et à mi-vie il vire au rouge et
accélère. Il garde la clé.

**L'esprit du donjon** entend et répond à voix haute : potion, épée, coffre,
bouclier, clé, torche, piège, jumeau, chemin percé, mur brisé ou dressé.

## Où sont les fichiers

    index.html            le jeu (≈3 850 lignes)
    three.module.js       le moteur 3D, en local — aucun appel réseau
    jsm/                  chargeurs : modèles (GLTF), ciels (RGBE), Spark
    assets/textures/      8 matières photographiées (Poly Haven, CC0)
    assets/nature-kit/    329 modèles (Kenney, CC0)
    assets/mini-dungeon/  mobilier de donjon (Kenney, CC0)
    assets/mini-forest/   forêt (Kenney, CC0)
    assets/polyhaven/     ciels panoramiques + un rocher scanné
    assets/splats/        une scène capturée en photos
    original.html         le jeu 2D d'origine, intact

Toutes les ressources sont en **CC0** : domaine public, usage commercial,
aucune attribution obligatoire.

## Réglages en direct

La console expose `window.D` : `D.joueur`, `D.lampe`, `D.lumieres`, `D.boss`,
`D.traiterChat('…')`, `D.voixDuMonde('…')`, `D.basculerVue()`, `D.allerA(5)`
pour sauter à un étage, `D.mur(x,z)` pour tester une collision.

Vider les compétences gardées : `localStorage.clear()` puis F5.
