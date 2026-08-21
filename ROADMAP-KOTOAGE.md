# KOTOAGE — feuille de route

Statuts : ✅ fait · 🔨 en cours · ⏳ en file · 📌 à ne pas oublier · ⛔ bloquant

## VERSION 1 (périmètre fixé par Patrick) → publication **itch.io**
Le village + les **5 étages** du donjon + le **mode entraînement**.

⛔ **JALON avant mise en ligne** : décider **ensemble** ce qui va **sur la tour (serveur)**
   — sauvegardes, scores, chat « transmission de pensée ». NE PAS publier avant cette décision.

## Gameplay / navigation
- ✅ Reprise au niveau atteint (`niveauMax` en sauvegarde).
- ✅ Plus de clé ; escaliers ; **cercle de téléportation** (motif magique, colonne bleue, marche dessus ou E).
- ✅ **Touche E** = interaction (coffre, portail ; extensible PNJ/forge).
- ✅ Coffres ouvrables sur E (posés aux cases `C` du plan).
- ✅ Histoire d'ouverture réécrite (sans la clé).
- ⏳ **Forge** : forger des armes (instruments : enclume, foyer) + chevaliers immobiles à l'entrée.
- ⏳ **IA mode entraînement** — voir `specs-ia-entrainement.md` (ciblage dynamique, combos, esquive AOE, ressources).

## Décors / assets (bpy, low-poly cel-shaded)
- ✅ **Entrée Colisée** v3 (`modeles/entree_colisee.glb`, 10 652 tris) — reste à **intégrer** dans le village.
- ✅ **Squelette de dragon** (`modeles/dragon_squelette.glb`, 2896 tris) — **intégré** à l'étage 5.
- ✅ **Chevalier en armure** (`modeles/chevalier.glb`, 722 tris) — pour la forge, à intégrer.
- ✅ Tonneau (`modeles/tonneau.glb`) — le jeu utilise déjà les props Quaternius.
- ⏳ **Intégrer le Colisée** comme bâtiment d'entrée du donjon (dans le village).
- ⏳ **Étage 2 = ville** style *City Street* (588 Mo) → **skybox** (léger) recommandé plutôt que jouable.
- ⏳ Meubler chaque étage (props Quaternius déjà chargés).

## Distribution
- ✅ Décision : **itch.io d'abord** (jeu web, 2€, test concept) → Steam plus tard (Electron + 100$).
- 📌 Copie du code : inévitable en web ; parade = logique sensible **sur la tour** + minification.

## Machine
- ✅ RAM 8→16 Go. ✅ Cache navigateur réglé (bouton « ↻ Recharger »).
- ⏳ **memtester** — en attente de `sudo apt install memtester` par Patrick.
