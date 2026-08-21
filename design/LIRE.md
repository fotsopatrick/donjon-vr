# Les tests de design de KOTOAGE

Le jeu a deux sortes de tests :

- **`test-jeu.js`** (à la racine) teste le **code** : est-ce que la logique marche ?
- **`design/`** (ce dossier) teste le **rendu** : est-ce que ce qu'on VOIT à
  l'écran colle à ce que Patrick aime — **cyberpunk néon la nuit, pas de plaine
  verte** ?

## Comment on regarde une image avec des chiffres

Un ordinateur ne « trouve » pas une image belle. Alors on compte les couleurs.
Chaque point de l'image est rangé dans une famille : **sombre** (le fond de
nuit), **cyan** et **magenta** (les néons), **ambre** (les fenêtres allumées),
**vert** (l'herbe — ce qu'on ne veut PAS), **ciel_pâle** (le vieux ciel bleu).

Ensuite deux calculs (dans `design_lib.py`) :

1. **À quelle famille de goût l'image ressemble le plus ?** On additionne les
   couleurs en donnant beaucoup de poids aux néons et au noir pour le
   « cyberpunk », et à l'herbe et au ciel clair pour la « plaine verte ». La plus
   grosse somme gagne. → `score_palettes()`
2. **Deux images se ressemblent-elles ?** On range toutes les couleurs dans des
   petits casiers et on regarde combien de casiers sont pareils. `0` = jumelles,
   `1` = tout les oppose. → `distance_hist()`

## Lancer

```sh
cd design
python3 tests-design.py            # capture l'arène en vrai et la note
python3 tests-design.py image.png  # note une capture déjà prise
```

La suite dit `8 réussis, 0 échoués` quand le rendu est bon. **Preuve que la porte
garde vraiment quelque chose** : lancée sur l'ancienne plaine verte
(`refs/ref-plaine-verte.png`), elle échoue à 7 sur 8 — elle refuse ce que
Patrick n'aime pas.

## Les références

- `refs/ref-cyberpunk.png` — le rendu validé (ce vers quoi on doit tendre).
- `refs/ref-plaine-verte.png` — le rendu rejeté (ce qu'on fuit).

Pour changer la cible du goût, on remplace ces deux images et on relance.
