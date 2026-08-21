# KOTOAGE — Ce que Patrick aime (référence design)
*maj 2026-08-20 — sert de cap pour tout choix visuel du jeu.*

## 1. Le style visuel qu'il veut
- **Stylisé Quaternius** = la base validée (avatars, props, village). Format .gltf/.glb.
- **VRoid** pour les avatars anime (« tous les designs j'adore »), format .vrm.
- **Anime cyberpunk / néon moderne** : le duel/entraînement est **cyberpunk**
  (néon cyan/magenta, ville futuriste, ambiance System Call / SAO).
  Ses mots : « je veux un truc **moderne**, **à la cyberpunk** ».
- **Cel-shading / rendu manga** (toon + contour noir).
- Intro façon **EA Sports** : un **lion** qui mange le logo Code nomi nomi
  (dédicace au **Cameroun**).

## 2. Ce qu'il DÉTESTE (ne jamais reproposer)
- **KayKit** et **Kenney** (« dégueulasse », « moche à 100 % »).
- Les **plaines vertes / nature fade** (« je déteste ça »).
- Les avatars **« carton »** et le **procédural cheap**.
- Le **générique** (ex. l'épée acier lambda — muée en lame d'énergie néon).

## 3. Gameplay / ambiance
- Combat **fluide façon Naruto Storm / Budokai Tenkaichi** (« son gameplay c'est
  le meilleur »), **combos**, **verrou de cible**, **mains OU épée**, **magie**.
- Mode **Entraînement** : arène cyberpunk vide, adversaire IA (mêmes
  compétences), **vie illimitée**, verrou façon Naruto. (fait, cette nuit)

## 4. Studios & artistes de référence (à suivre / s'en inspirer)
- **Studio Trigger** (Cyberpunk Edgerunners) — IG/X @trigger_inc
- **Arc System Works** (Guilty Gear, DBFZ, cel-shading) — IG @arcsystemworksu / X @ArcSystemWorksU
- **CyberConnect2** (Naruto Storm) — X @cc2information
- **ufotable** (Demon Slayer, VFX lumineux) — IG @ufotable_inc / X @ufotable
- **Spike Chunsoft** (Budokai Tenkaichi / Sparking Zero) — X @DBSparkingZER0
- **SAO / A-1 Pictures** — via Aniplex USA
- Concept cyberpunk : Beeple, Filip Hodas, Ash Thorp, Khyzyl Saleem, Maciej
  Kuciara, Vitaly Bulgarov.

## 5. Assets précis qu'il a choisis (à intégrer)
- **Sa maison = gaming room free3d** (id 34242) : derrière **une porte d'un
  bâtiment du village**, avec un **indicateur** sur la porte.
- **Paysage extérieur = BlendSwap 30474** : remplacer l'extérieur par ce
  paysage exact.
- **Animaux / forêt du donjon = Sketchfab (tag blender)** — « bien dessinés ».
- **Blendkit** : il **adore**, mais **seulement si léger**. Ses 2 scènes témoins
  (Japanese Laundry Room, Winter Frost Meadow) sont **Full Plan (payantes),
  198–347 Mio, 558k polygones, .blend → BEAUCOUP TROP LOURD** pour le web. À
  garder comme **références visuelles** ; in-game, uniquement les assets
  **Free + légers** convertis en glTF.

## 6. Réalité technique (contrainte « léger » sur nomi)
- Tout asset **.blend** (Blendkit, BlendSwap, free3d, Sketchfab) doit être
  **exporté en glTF/GLB** puis **allégé** (décimé à quelques milliers de
  triangles, textures réduites). Blender requis (**pas installé sur nomi** au
  20/08 ; à installer, ou convertir sur la tour).
- **Portes fermées** : les téléchargements free3d / Sketchfab / Blendkit /
  BlendSwap sont **derrière une connexion**. **Patrick télécharge** (je ne crée
  pas de compte et ne saisis pas d'identifiants) ; ensuite je convertis, allège
  et branche dans le jeu.

## 7. Comment on valide un design (déjà en place)
- **Tests de design** `~/donjon-vr/design/` : mesurent la palette d'une capture
  et la comparent au goût (cyberpunk néon OUI, plaine verte NON). L'arène passe
  8/8 ; l'ancienne plaine verte échoue 7/8. On peut caler la cible sur une
  image de référence (ex. un studio ci-dessus).
