# Étude Braignak — les mouvements des avatars (21/08)

Méthode PRÉDATEUR de Braignak : observer ce qui existe dehors, relever la
licence AVANT tout, ne jamais répondre de mémoire, conclure avec une confiance.

## La cible observée
L'exemple officiel de la bibliothèque `three-vrm` (celle qui affiche nos
personnages VRoid) : `loadMixamoAnimation.js`. Il recopie une animation faite
pour un squelette étranger vers un personnage VRM. Lu sur le dépôt officiel
(pixiv/three-vrm) — pas de mémoire, la page a été lue aujourd'hui.

## Licences (relevées d'abord, règle Braignak)
- `three-vrm` et son exemple : **MIT** → libre, réutilisable.
- Animations Quaternius (Universal Animation Library) : **CC0** → domaine public.
- Nos personnages VRoid : fournis par Patrick.
→ Rien de contaminant. Confiance licence : 1.0.

## Le geste (tactique) — la formule exacte de l'exemple officiel
Pour chaque image-clé de rotation d'un os :
`nouvelle = (rotation_repos_monde_du_parent) × (rotation_du_clip) × (inverse_rotation_repos_monde_de_l_os)`
Pour la position des hanches : multiplier par `hauteur_hanches_VRM / hauteur_hanches_source`.
Les pistes sont renommées vers les os « normalisés » du VRM
(`humanoid.getNormalizedBoneNode(nom).name`).

## La manœuvre (opérationnel) — chez nous
- Source : les clips de l'ancien avatar (Idle_Loop, Walk_Loop, Sprint_Loop,
  Sword_Attack…) portés par le squelette de `perso-quaternius.glb`
  (os : pelvis, spine_01..03, upperarm_l, thigh_l, calf_l…).
- Table de correspondance vers le VRM : pelvis→hips, spine_01→spine,
  spine_02→chest, spine_03→upperChest, neck_01→neck, Head→head,
  clavicle→shoulder, upperarm→upperArm, lowerarm→lowerArm, hand→hand,
  thigh→upperLeg, calf→lowerLeg, foot→foot, ball→toes (gauche/droite).
- Le lecteur d'animation (mixer) se branche sur la scène du VRM ; après chaque
  mise à jour du mixer, `vrm.update(dt)` propage vers le vrai squelette.
- Ancien VRM (version 0) : inverser les signes x et z (rotation ET position).

## La raison (stratégique)
Patrick a validé les mouvements de l'ancien avatar. On les REPREND tels quels
sur les VRoid au lieu d'inventer une animation à la main (l'« épouvantail »).
Une animation validée réutilisée > une animation inventée.

## Preuves exigées (portes)
- Tests automatiques : chaque avatar bouge avec amplitude en marchant,
  le bras bouge à l'attaque (tests/runtime.js).
- Captures avant/après.
- Dernier mot : l'œil de Patrick.

Confiance de l'étude : 0.85 (la formule vient de la source officielle ; le
risque restant est la pose de repos de notre squelette source).
