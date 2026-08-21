# Projet KOTOAGE / « Le Petit Donjon » — règles de travail

> Ce projet suit **les mêmes règles que tous les autres projets de Patrick**.
> Le fait que ce soit « un jeu » ne suspend RIEN. Lire ce fichier au départ de
> chaque session, comme le CLAUDE.md de la tour.

## Règle nº1 — nomi est une machine FAIBLE (ne pas la faire ronfler)

Le jeu se développe en local sur **nomi**, une machine modeste. Tout ce qui
suit est non négociable (voir mémoire [[pas-de-sous-agents-sur-nomi]] et
[[chrome-headless-sature-nomi]]) :

- **Un seul Chrome de test à la fois, fermé AUSSITÔT.** Un chrome headless qui a
  chargé le jeu rend le WebGL en boucle à fond ; en empiler plusieurs a fait
  monter le CPU à **1135 %** et le ventilo a hurlé (20/08/2026). Après chaque
  capture/test : `pkill -9 -f "user-data-dir=/tmp/chrome-<profil>"`.
- **Avant toute action, se poser la porte : « est-ce que ça charge nomi ? »**
  (rendu lourd, boucle, gros process). Si oui → alléger ou renoncer.
- Cibler les kills par `user-data-dir=/tmp/chrome-*` pour ne JAMAIS toucher le
  Chrome de Patrick (profil `~/.config`) ni sa fenêtre de jeu.
- `tests/run.sh` tue déjà son chrome à la fin → le préférer aux captures manuelles.

## Règle nº2 — voir avant de coder, tester ce qui compte

- **TDD / preuve** : écrire/faire tourner un test AVANT de conclure. Ne jamais
  dire « c'est corrigé » sans l'avoir vu (capture) ou mesuré (assertion).
  Système de test rejouable : `bash tests/run.sh` (statiques + comportement).
- **Le cache Chrome ment.** Il ressert l'ancienne version → un bug « qui revient »
  est souvent le cache. Servir avec `serveur-nocache.py`, recharger en Ctrl+Shift+R.

## Règle nº3 — dépôt sur le VPS, jeu en local

- Le **jeu tourne uniquement en local** (nomi, serveur 8099). Il ne va **jamais**
  sur le VPS (le VPS ne peut pas le faire tourner).
- Le **dépôt git** vit sur le VPS (worktree `chantiers-tour/kotoage`, branche
  `chantier/kotoage`). On committe là. **Pas de GitHub** sans consigne explicite.
- Ne pas committer les 388 Mo de packs sources bruts (`assets/` téléchargés) —
  seulement le vrai travail (code, voix, modèles bpy, tests, specs).

## Règle nº4 — méthode et comportement (comme partout)

- Réponses courtes, une étape à la fois (mémoire [[reponses-courtes]]).
- Méthode scientifique sur un problème (deux hypothèses, l'observation qui tranche).
- Heure toujours en Europe/Paris. Lire une source jusqu'au bout avant de conclure.
- Les goûts assets de Patrick : Quaternius + **VRoid** oui ; il veut du **style
  anime**. Voir [[gout-assets-3d-patrick]] et [[gout-arene-cyberpunk]].

## État / specs du projet
`specs-*.md` (combat DBZ → mana pas ki, éclairage duel, mage, pièges…),
`ROADMAP-KOTOAGE.md`, `CIRCUITS-JEU.md`. Voix clonée : dossier `voix/`, pipeline
dans `~/voix-locale/` (Coqui XTTS local).
