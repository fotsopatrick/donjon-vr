# Circuits & leçons — conception du jeu KOTOAGE

But : capitaliser ce qu'on apprend pour aller plus vite. Un **circuit** = un chemin
d'étapes avec des **portes** (une porte qui refuse fait son travail). Les **leçons**
sont les pièges déjà payés — on ne les repaie pas deux fois.

---

## CIRCUIT 1 — Piloter & vérifier le jeu (le harnais)
Le jeu est un `index.html` servi en local. Pour le voir/tester sans dépendre de Patrick :

1. **Serveur** : `python3 -m http.server 8099` dans `~/donjon-vr` (déjà lancé en général).
2. **Chrome avec débogage** :
   `google-chrome --user-data-dir=~/.config/chrome-jeu --remote-debugging-port=9222 --disk-cache-size=1 http://127.0.0.1:8099/index.html`
3. **Harnais** `cdp-jouer.js` — pilote par le protocole DevTools :
   `node cdp-jouer.js '[{"nav":"#village"},{"wait":6000},{"key":"KeyW","ms":800},{"eval":"..."},{"shot":"/tmp/x.png"}]'`
   Actions : `nav` (recharge vraiment via about:blank), `wait`, `key` (maintien ms), `click:[x,y]`, `eval`, `shot`.
4. **Lire** : `Read` sur le PNG (je vois enfin le rendu), `eval` pour l'état, la console via `cdp-check.js`.

**Porte** : si le screenshot montre autre chose que prévu, on ne conclut pas — on `eval` l'état
réel (`document.getElementById('etage').textContent`, `window.D.joueur`, `window.D.ennemis.length`).

## CIRCUIT 2 — Nouvel asset 3D (bpy → jeu)
1. Script `blender/<nom>.py` : modéliser en **low-poly cel-shaded** (couleurs plates), pas de Kenney.
2. `blender --background --python <nom>.py` → export `.glb` dans `modeles/` + rendu Workbench d'aperçu.
3. **Porte perf** : viser < ~15 000 triangles, `.glb` léger (Ko). Sinon décimer / skybox.
4. Déclarer dans `A_CHARGER` (`nom: 'modeles/<nom>.glb'`), placer via `MODELES.<nom>.clone(true)`.
5. `node test-jeu.js` (60/60) puis CIRCUIT 1 pour voir en jeu.
   **Porte machine** : jamais de rendu Cycles lourd (City Street = 2,5 M tris) pendant que Patrick joue → ça chauffe.

## CIRCUIT 3 — Nouvelle feature gameplay
1. Écrire la **spec** (`specs-*.md`) au plus près des mots de Patrick.
2. Éditer `index.html`, réutiliser l'existant (chercher avant de créer).
3. **Porte syntaxe/invariants** : `node test-jeu.js` doit rester à 60/60.
4. **Porte visuelle** : CIRCUIT 1 (screenshot + eval), corriger, re-vérifier. Ne jamais affirmer « ça marche » sans avoir vu.
5. Valider avec Patrick.

---

## LEÇONS (pièges déjà payés)
- **Le hash ne recharge pas le code.** Naviguer `index.html#village` puis `#donjon` = juste un
  `hashchange`, le module JS reste en mémoire (ancienne version). → Forcer `about:blank` puis l'URL.
- **Cache Chrome.** Il ressert l'ancien `index.html`. → `--disk-cache-size=1` + bouton « ↻ Recharger » au titre.
- **InstancedMesh non borné = freeze.** Une tuile mal mesurée → des dizaines de milliers d'instances → gel.
  → Toujours borner (`Math.min(60, …)`), rejeter les mesures douteuses, retomber sur un plan de secours.
- **CDP en arrière-plan throttle à ~10 fps.** Les transitions (titre → jeu) et chargements sont lents à capturer → attendre 6–11 s.
- **`window.D`** expose l'état pour le debug (joueur, ennemis, grid, etat, arme, avatar…). S'en servir pour trancher.
- **Vue 1ʳᵉ personne** : `avatar.visible=false`, l'arme tenue reste visible — surveiller son échelle/placement.
- **`niveau` vaut 1 par défaut** au chargement → un `setTimeout` armé à ce moment peut se déclencher au mauvais endroit.
  Toujours revérifier l'état DANS le timer (`if(niveau===1 && etat==='jeu')`).
- **Extension Claude non connectée** → je ne peux pas piloter la vraie fenêtre de Patrick ; le harnais CDP est l'alternative.

## BUGS VILLAGE en cours (à finir)
- Histoire du donjon qui s'affichait au village → correctif posé (revérif dans le timer), à confirmer.
- Épée du joueur géante au premier plan (vue 1ʳᵉ personne) → à régler.
- Sol du village trop sombre (dalles Quaternius + éclairage) → à régler.
- Texte du titre « trouve la clé, ouvre la porte » → obsolète (plus de clé), à réécrire.
