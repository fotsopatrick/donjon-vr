# CIRCUIT — Ajouter un avatar (VRoid / VRM) à KOTOAGE

> Gouvernance demandée par Patrick (21/08). Un avatar ne « passe » que s'il a des
> **mouvements amples** ET les **combos de base**. Un avatar figé (« bâton de bois »)
> est REFUSÉ par la porte. Une porte qui refuse fait son travail.

## Les étapes (dans l'ordre, aucune sautée)

1. **Déposer** le `.vrm` dans `assets/vrm/` (Patrick le fournit — les sites bloquent le téléchargement auto).
2. **Déclarer** dans `A_CHARGER` (nom → chemin `.vrm`). Les avatars secondaires vont en `DIFFERES`
   (chargés en arrière-plan) ; un seul VRM joueur en priorité (selon la classe) sinon le démarrage rame.
3. **Charger** via le plugin VRM (déjà branché : `VRMLoaderPlugin`) → `gltf.userData.vrm`.
   Ne PAS toonifier (garder les matériaux MToon). Orienter `rotation.y = Math.PI` (le VRM regarde +Z).
4. **Brancher l'animation** : appeler `animerVRM(vrm, dt, t, marche, court, attaque, src)` sur cet avatar
   à chaque frame. Pour un clone (villageois) → gérer l'accès aux os.

## LES PORTES (garde-fous — rien ne passe si une est ROUGE)

- **Porte MOUVEMENTS AMPLES** ⛔ : l'avatar DOIT bouger nettement en marchant (bras qui balancent large,
  grande foulée, contre-rotation buste/hanches) et respirer/bouger au repos. Preuve : test d'amplitude
  automatique (`tests/run.sh` : les os changent de rotation entre 2 instants de marche) **+** capture
  validée par l'œil Gemini (Porte visuelle). Un avatar figé = REFUSÉ.
- **Porte COMBOS DE BASE** ⛔ : la frappe (`frapper()`) doit produire un geste ample (bras qui fend,
  torsion du buste) et l'enchaînement (combo) doit s'incrémenter. Pas d'avatar qui « tape mou ».
- **Porte PLACEMENT** ⛔ : l'avatar n'apparaît PAS dans un mur ni collé au décor. Vérifié en jeu.
- **Porte VISUELLE (Gemini)** : `python3 gemini-critique.py capture.png` → l'œil externe valide le rendu.
- **Porte PATRICK** : le dernier mot.

## Rappel dur
- On ne committe JAMAIS un avatar qui n'a pas franchi les portes MOUVEMENTS + COMBOS.
- On ne dit JAMAIS « fait » sans capture validée.
- Passer par `bash garde-fou.sh <captures>` avant chaque commit d'avatar.

Voir [[la-tour-est-un-rpg]] (les portes sont des épreuves), le CLAUDE.md du projet, et
`garde-fou.sh` (le circuit exécutable).
