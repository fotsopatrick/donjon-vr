# La pile — ce que Patrick a demandé, dans l'ordre

**Règle de tri**, du plus urgent au moins urgent :

1. **Ça casse le jeu** — on ne peut plus jouer, ou on perd du travail.
2. **Ça gâche le jeu** — on peut jouer, mais c'est laid ou ça rame.
3. **Ça manque** — une chose demandée qui n'existe pas encore.
4. **Ça aiderait** — un outil, un confort.

À égalité, le plus ancien passe devant. Patrick peut couper la file en écrivant
**« d'abord : … »** — ça passe en tête, quoi qu'il arrive.

---

## 1 — Ça casse le jeu

- [ ] **Étage 1 du donjon : les cercles de téléportation sont inatteignables.**
      Patrick, 22/08 : « t'as retiré les murs sans donner la possibilité
      d'atteindre les cercles ». On ne peut plus descendre.

## 2 — Ça gâche le jeu

- [ ] **Le village tourne à 2 images par seconde** (1395 appels de dessin).
      Mesuré le 22/08. C'est ce qui rend tout mou.
- [ ] **Le « truc noir » sur les épaules des villageois.** Mesuré : ce n'est PAS
      une ombre (zéro ombre sur les 8 habitants). Il me faut une photo de Patrick,
      ou savoir si c'est le garçon ou la fille.
- [ ] **Le colisée à l'entrée du donjon** : assemblage incomplet, plein de vides.
- [ ] **La photo du ciel posée au sol** en allant vers le deuxième village.

## 3 — Ça manque

- [ ] **La tenue façon Kirito** + une épée du même genre. Sans copier l'anime.
- [ ] **Les cris de combat** : Patrick doit déposer des fichiers libres dans
      `cris/fille/coup1-3.mp3` et `cris/garcon/coup1-3.mp3`. Le branchement est fait.
- [ ] **De vrais mouvements de vol** (où en trouver, ou comment les fabriquer).

## 4 — Ça aiderait

- [x] **La carte vivante du jeu** — page avec onglets par type et commentaires par
      zone, plus un raccourci sur le bureau. FAIT le 22/08.
- [ ] **L'éditeur de carte en 2D** : installer **Tiled** (gratuit, mapeditor.org) et
      faire lire son fichier par le jeu. Patrick dessine, le jeu modélise.
- [ ] **Le garde-fou de repos** : à une heure choisie, tout se sauvegarde, on écrit
      ce qui a été fait, la journée est déclarée finie.
- [ ] **opencode sans fuite vers DeepSeek** : soit un modèle qui tourne sur malo,
      soit opencode pointé sur Anthropic. Un filtre qui « surveille » est une illusion.
- [ ] **Le ménage sur la tour** : disque plein à 90 %, 7,6 Go libres.

---

## Fait, et prouvé

- Vol : le corps prend une vraie pose, il respire, il pique du nez, il s'incline.
- Demi-tour en reculant (le corps a son cap, séparé de la caméra).
- Villageois : les deux alphabets d'os, bras rabattus le long du corps.
- Deux épées (touche X) avec l'escrime à deux lames.
- Choc d'épées dans l'arène : duel de mana, étincelles, gagnant/perdant.
- Étage 1 plus clair, plafond à 30 m.
- Dépôt du jeu sauvegardé sur la tour (`~/depots/kotoage.git`).

## Vus sur la photo de Patrick (22/08, après le fix de l'écran noir)
- [ ] **Villageois bras en croix** (épouvantail) : rabattreLesBras ne les attrape
      pas tous. Vérifier que trouverOsCorps trouve bien lUA/lLA sur CES villageois
      (archer = model1.vrm style Mixamo) et que rabattreLesBras s'applique.
- [ ] **Ombre noire en étoile** sous un personnage (femme en bleu) : ombre portée
      dure. Dehors les ombres sont censées être coupées — d'où vient celle-ci ?
      (peut-être un PNJ avec castShadow, ou un faux plan d'ombre sous les pieds.)

## GAGNÉ le 22/08
- [x] **Écran noir / on ne peut plus bouger** : colliders de springbone cassés
      lus au dessin. neutraliserColliders les retire. PROUVÉ par la photo de
      Patrick (il marche, 32 i/s). Version v22i-collider.
