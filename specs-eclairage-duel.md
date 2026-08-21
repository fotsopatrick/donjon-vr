# Éclairage « affrontement » bleu froid / rouge chaud (demande Patrick, 20/08 — PAS urgent)

Réf : capture d'anime envoyée par Patrick — deux personnages face à face, l'un
baigné de **bleu glacé** (rim light bleu électrique, œil bleu lumineux), l'autre
de **rouge/orange feu** (rim light chaude, œil rouge), fond en **dégradé
chaud↔froid** au centre, couleurs très **saturées**, fort **contraste**, ambiance
combat épique.

## À appliquer où
Le **mode duel / arène** en priorité (deux combattants opposés = pile ce visuel).
Rejoint [[gout-arene-cyberpunk]] (néon moderne, pas plaine verte).

## Recette technique (Three.js, on a déjà le cel-shading)
1. Deux `DirectionalLight` opposées :
   - côté joueur : couleur bleu électrique (~0x3a7bff), depuis la gauche.
   - côté adversaire : couleur rouge/orange (~0xff5a1e), depuis la droite.
   - intensités fortes, ambiante basse pour garder le contraste.
2. Rim light : lumières placées DERRIÈRE chaque combattant vers la caméra
   (liseré lumineux sur la silhouette).
3. `MeshToonMaterial` conservé ; `emissive` sur les yeux / le feu + petit bloom.
4. Fond : plan/skybox en dégradé bleu (côté joueur) → rouge (côté adversaire).
5. `toneMappingExposure` un peu haut, couleurs saturées.

## Statut
⏳ à faire APRÈS la voix. Ne pas casser l'arène cyberpunk existante — c'est une
passe d'éclairage, testée au harnais (screenshot avant/après).
