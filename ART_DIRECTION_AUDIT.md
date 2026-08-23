# ART_DIRECTION_AUDIT.md — DONJON (jeu uniquement, pas le Studio)

Date : 23/08/2026 · Direction cible : **Stylized Realistic Fantasy**
(SAO / Slime comme références de cohérence et d'immersion, pas de copie).

Ce rapport identifie CE QUI produit le look « cartoon / low-poly / carton /
plastique » dans le pipeline de rendu actuel, avec une cause technique pour
chaque problème. Aucune modification n'a été faite pendant cet audit.

---

## 0. Vue d'ensemble du pipeline actuel

| Étage | Rendu | Matériaux | Éclairage |
|---|---|---|---|
| Village (dehors) | PBR (maisons) + **Lambert** (sol/rues/montagnes) + toon hérité sur quelques éléments | textures photo (Lambert) + Quaternius PBR (maisons) + canvas (toit/bois) | hemi + soleil + ambiance 1.4, ombres douces ON, ACES 1.12 |
| **Donjon (1-5)** | **CEL-SHADING : MeshToonMaterial + 4 paliers + CONTOURS NOIRS** | canvas (pierre, sol) + primitives (MAT.*) | hemi + soleil + ambiance 0.5, ombres douces ON, ACES 1.3 |
| Arène | néon (MeshStandard + MeshBasic émissif) | primitives | projecteur + 2 lumières colorées |

Le cœur du problème est le **donjon** (où le joueur passe la majorité du
temps) : il applique `styliser(monde, 0.02)` en fin de construction, qui
convertit **tout** (murs, sol, décor, ennemis, props) en MeshToonMaterial à
4 paliers et ajoute une coque de contour noir (`cerner`) sur chaque mesh.

---

## 1. Problèmes identifiés (cause → correction → coût → priorité)

### P1 — CEL-SHADING 4 PALIERS (la signature « cartoon »)
- **Problème** : bandes de lumière dures (4 marches) sur toutes les surfaces du donjon.
- **Cause technique** : `nuancierToon(4)` (gradient 4 valeurs, plancher MIN_TOON 0.40)
  appliqué par `styliser(monde, 0.02)` → MeshToonMaterial sur toute la scène donjon.
- **Impact visuel** : l'éclairage « par paliers » est LA signature du style dessiné.
- **Correction** : ne plus convertir en MeshToon. Remplacer la passe toon par une
  passe **PBR-relief** : conserver MeshStandardMaterial (ou Lambert éclairé par
  sommet pour les surfaces simples) + normal/bump + ACES + ombres douces.
  Plancher d'éclairage : relever l'ambiance du donjon (~0.5 → 0.9) pour éviter
  le noir bouché, sans aplatir.
- **Coût perf** : MeshStandard éclaire par pixel (plus cher que Lambert) ; les
  murs sont **instanciés** (peu d'appels). Estimation : −5 à −15 % i/s dans le
  donjon selon le GPU ; compensable en gardant Lambert pour les grandes surfaces
  (sol/plafond) et Standard pour les props/ennemis proches.
- **Priorité** : **1 (bloquant)**.

### P2 — CONTOURS NOIRS (`cerner`)
- **Problème** : trait noir autour de chaque mesh (murs, décor, ennemis).
- **Cause technique** : `cerner()` pose une coque inversée gonflée le long des normales.
- **Impact visuel** : l'outline anime → « jeu dessiné ».
- **Correction** : supprimer les contours du donjon (et du décor), les garder
  éventuellement très fins uniquement sur les personnages anime si on le souhaite.
  Supprimer les coques = **moins de géométrie** (gain de perf).
- **Coût perf** : **gagnant** (moitié moins de meshes sur le décor/ennemis).
- **Priorité** : **1 (avec P1, ils vont ensemble)**.

### P3 — TEXTURES PROCÉDURALES CANVAS + BOOST DE RELIEF
- **Problème** : surfaces « carton » (pierre plate, sol plat, tuiles lisses).
- **Cause technique** : textures générées par canvas (texturePierre, textureSol,
  texRelief…) de petite taille, tuilées ; le bump existant (texRelief) est
  trop faible et perdu par la conversion toon (MeshToon ignore le relief).
- **Impact visuel** : absence de micro-détail → matériaux « plastiques ».
- **Correction** : (a) basculer les grandes surfaces du donjon sur les textures
  PHOTO existantes (`mur-pierre.jpg`, `sol-terre.jpg`, `paves.jpg`) ; (b) générer
  à la volée des **normal maps** depuis ces textures (fonction de conversion) pour
  un relief perceptible ; (c) augmenter la résolution des textures procédurales
  restantes (512 → 1024) avec variation de teinte par tuile (pré-calculée).
- **Coût perf** : normal map = une lecture de texture supplémentaire par pixel
  (modéré) ; textures 1024 sur les murs instanciés = mémoire raisonnable.
- **Priorité** : **2**.

### P4 — SOL UNIFORME (donjon ET dehors)
- **Problème** : grande surface homogène, pas de transition, pas d'usure.
- **Cause technique** : sol = un seul plan avec une texture tuilée répétée sur
  tout l'étage ; au dehors, tuiles vFloor sur 145 m.
- **Impact visuel** : « dalle posée », pas un lieu.
- **Correction** : (a) varier la teinte par zone (vertex colors / 2e plan de
  mélange) ; (b) chemins d'usure (bandes plus sombres/plus claires) le long des
  passages ; (c) petits détails posés (pierres, débris, flaques) en instancing.
- **Coût perf** : faible (2 plans + instancing existant).
- **Priorité** : **3**.

### P5 — VÉGÉTATION LOW-POLY
- **Problème** : arbres très géométriques (cônes/sphères bpy), répétitions visibles.
- **Cause technique** : `modeles/arbre_feuillu.glb` / `arbre_conifere.glb` =
  modèles basse définition à matériau simple ; semés par instancing (bien) mais
  sans variation de silhouette ni feuillage crédible.
- **Impact visuel** : « sapins de jeu de société ».
- **Correction** : (a) améliorer le MATÉRIAU (feuillage avec variation de teinte +
  normal/bump, tronc texturé) ; (b) plusieurs essences/silhouettes réelles
  (bpy : feuillu, conifère, chêne) avec variations d'échelle/rotation ; (c)
  sous-bois (buissons, fougères, rochers, herbes) pour casser la répétition ;
  (d) à terme, remplacer les modèles les plus pauvres par des GLB stylized-realism.
- **Coût perf** : instancing conservé (1 appel/essence) ; matériaux + normal
  modérés.
- **Priorité** : **4**.

### P6 — MATÉRIAUX NON DIFFÉRENCIÉS (plastique)
- **Problème** : pierre/bois/métal se ressemblent (même roughness ~0.85, pas de
  metalness, couleur uniforme).
- **Cause technique** : table `MAT.*` du donjon = MeshStandardMaterial à couleur
  unie, roughness quasi identique ; les props Quaternius sont ensuite toon-ifiés
  (aplatissement).
- **Impact visuel** : tout a l'air du même plastique.
- **Correction** : après P1 (fin du toon), différencier : bois rugueux + grain
  (texture `bois.jpg`), métal avec metalness + spéculaire, pierre avec joints +
  relief, tissu mat. Utiliser `material_lib` (déjà en place côté world-builder)
  comme référence des valeurs, déclinées dans le jeu.
- **Coût perf** : négligeable (mêmes shaders, valeurs différentes) ; metalness
  sans env-map reste discret (ok).
- **Priorité** : **2 (avec P3)**.

### P7 — ÉCLAIRAGE PLAT / PAS DE VOLUME
- **Problème** : le donjon semble plat malgré les ombres ; ambiance 0.5 + hemi.
- **Cause technique** : avec le toon, la lumière tombe en paliers → pas de
  dégradé de volume ; l'ambiance faible écrase le contraste local.
- **Impact visuel** : absence de profondeur, objets « posés ».
- **Correction** : (a) après P1, l'ACES + PBR redonnent le dégradé ; (b) relever
  l'ambiance à ~0.9 et le hemi du donjon ; (c) conserver les 6 lumières locales
  (torches) mais les laisser faire du volume (atténuation douce, décay 1.6) ;
  (d) NE PAS ajouter de lumières en masse.
- **Coût perf** : les 6 lumières dynamiques déjà budgétées ; pas d'ajout.
- **Priorité** : **1 (découle de P1)**.

### P8 — ANTI-ALIASING DÉSACTIVÉ
- **Problème** : arêtes crénelées sur les silhouettes (look « prototype »).
- **Cause technique** : `renderer = new THREE.WebGLRenderer({ antialias:false, pixelRatio:1 })`.
- **Impact visuel** : dents de scie, accentue le low-poly.
- **Correction** : `antialias:true` (et pixelRatio 1 conservé). Si le coût est
  trop élevé sur le GPU intégré, compenser par une légère supersampling sur le
  casque/écran ou accepter pixelRatio 1 avec AA.
- **Coût perf** : AA = filtrage MSAA, coût modéré (mesure nécessaire).
- **Priorité** : **2**.

### P9 — PERSONNAGES / CRÉATURES vs MONDE
- **Problème** : personnages anime (VRoid + contours) détachés du monde ;
  certaines créatures flottent ou paraissent plates.
- **Cause technique** : VRoid sans réglage d'éclairage partagé ; les créatures
  B/C (spectre/rat) ont été refaites (component system) mais le toon du donjon
  les aplatit encore ; le contact shadow n'existe que sous forme d'ombre portée.
- **Impact visuel** : « autre univers ».
- **Correction** : (a) après P1, les créatures PBR seront éclairées comme le
  monde ; (b) ajouter un **contact shadow** (disque doux) sous chaque créature/
  personnage en plus de l'ombre portée ; (c) harmoniser l'exposition des VRoid
  (tonemapping global déjà partagé — vérifier l'ambiance).
- **Coût perf** : disque = 1 mesh alpha par créature (faible).
- **Priorité** : **3**.

### P10 — PROFONDEUR ATMOSPHÉRIQUE
- **Problème** : arrière-plan « collé » (le village s'arrête net ; le château est
  une bande).
- **Cause technique** : fog FogExp2 léger au dehors (0.007) ; le château est
  composé dans la toile du ciel (bande), les montagnes sont des cônes.
- **Impact visuel** : pas d'impression que le monde continue.
- **Correction** : (a) brume de distance légère et TEINTÉE (pas un mur) pour
  fondre montagnes/château ; (b) dégradé du relief par distance (le fog ACES
  s'en charge) ; (c) NE PAS ajouter de brouillard massif.
- **Coût perf** : nul (le fog est déjà calculé).
- **Priorité** : **3**.

### P11 — CIEL / SOLEIL (dehors)
- **Problème** : le ciel passe encore parfois pour un décor séparé (soleil déjà
  adouci en dégradé radial en Phase A — reste à valider la cohérence).
- **Cause technique** : toile du ciel = canvas dégradé + château composé en bande.
- **Impact visuel** : rupture potentielle à l'horizon (atténuée par le fondu alpha).
- **Correction** : valider sur captures ; si rupture → fondre davantage la bande
  et aligner la couleur de la brume d'horizon avec la base du dégradé.
- **Coût perf** : nul.
- **Priorité** : **3**.

---

## 2. Synthèse — les 5 problèmes prioritaires

| # | Problème | Cause racine | Coût | Ordre |
|---|---|---|---|---|
| 1 | Look cartoon | **Cel-shading 4 paliers + contours noirs** (`styliser`/`cerner`) | −5 à −15 % i/s donjon (compensé par la suppression des contours) | **1** |
| 2 | Surfaces « carton » | textures canvas plates + bump perdu par le toon | modéré (normal maps) | 2 |
| 3 | Plastique non différencié | MAT.* uniformes + toon qui aplatit | nul (valeurs) | 2 |
| 4 | Végétation low-poly | modèles bpy pauvres + matériau simple | faible (instancing conservé) | 3 |
| 5 | Monde plat / profondeur | ambiance faible + arrière-plan collé + AA off | faible | 3 |

**Ordre d'implémentation** : P1+P2 (dé-toon + sans contours) → P3/P6
(textures photo + normal maps + matériaux différenciés) → P7/P8 (éclairage +
AA) → P4/P5 (sol + végétation) → P9/P10/P11 (personnages, atmosphère, ciel).

---

## 3. Ce qui est déjà bon (à conserver)
- **ACESFilmic + exposition** : base cinématique correcte.
- **Ombres PCFSoft** : douces, fenêtre ±48 qui suit le joueur.
- **Sky System** : pilote la lumière, presets prêts, soleil déjà adouci.
- **Instancing** (murs, arbres, tuiles) : la bonne approche perf.
- **Composants réutilisables** (puits, clôtures, chemins, créatures).
- **Fog par étage** : base d'atmosphère présente.

## 4. Règle de travail
- ZONE PILOTE d'abord : place → rue → route du donjon → entrée (dehors) + un
  étage du donjon (é.1).
- Baseline = captures d'inspection actuelles (référence de non-régression).
- À chaque étape : baseline → modification → capture → comparaison → perf →
  validation → commit local. Aucun push.
