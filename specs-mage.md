# Classes jouables : Chevalier & Mage (demande Patrick, 20/08)

Au départ, **choisir sa classe** : Chevalier ou Mage.

## Chevalier (existant)
Combat épée + poings, dash (foncer), verrou de cible.

## Mage (à construire)
- **Coups de poing** — combat physique de base (comme le chevalier au corps-à-corps).
- **Charge d'énergie** — maintenir pour charger (façon Naruto Storm), libère des sorts plus forts.
- **Sorts** — commencer par le **FEU**.
- **Feu au sol persistant** — quand le feu touche le sol, il **brûle au sol**, **inflige des dégâts** à qui s'y trouve,
  puis **disparaît petit à petit** (se consume).
- **Animations** nécessaires : feu (projectile/flammes), **brûlure** (sur le joueur et les monstres),
  monstres qui réagissent au feu.

## Existant à réutiliser
- `lancerProjectile('feu'|'eau'|'vent')`, incantation feu (touche V), système `pouvoirs`, flammes en sprites/canvas.
→ structurer en classe Mage, ajouter la charge d'énergie et la zone de feu au sol.
