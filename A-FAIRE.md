# La pile — ce que Patrick a demandé, dans l'ordre

## EN PREMIER à la reprise (Patrick, 22/08)
- [ ] **L'ENTRÉE DU DONJON EST RATÉE** (vue sur la photo du vol : grande forme
      beige plate en haut à droite, comme un carton de travers, pas un bâtiment).
      C'est le modèle entreeColisee, troué/incomplet. Deux voies :
      1) le CACHER (ne pas le poser) — vite fait, l'escalier/cercle reste pour
         descendre ; une entrée absente est moins laide qu'une entrée ratée.
      2) le REFAIRE propre en pierre (arche + colonnes, sans trous) dans le jeu.
      Demander à Patrick laquelle il veut.
- [ ] **LE VOL N'EST PAS NATUREL** : le corps reste tout droit, debout dans les
      airs, jambes qui pendent. Il doit PLANER : buste penché en avant, bras
      ouverts en arrière, jambes tendues derrière (poserCorpsEnLAir existe mais
      la pose ne s'applique pas visiblement en vol — vérifier pourquoi : le mixer
      des vraies animations écrase peut-être la pose, ou avatar.rotation.x/tangage
      n'est pas posé). Régler AVANT tout le reste.
      IDÉE DE PATRICK (meilleure piste) : des AILES D'ELFE qui se DÉPLOIENT
      quand on décolle, avec une animation de battement. L'œil regarde les ailes,
      plus la pose raide du corps. Chercher des ailes CC0 (domaine public) :
      Quaternius, Sketchfab (filtre CC0), Poly Pizza. Les attacher au dos (os
      upperChest/spine), cachées au sol, ouvertes en vol, qui battent doucement.


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
