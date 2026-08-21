# Vol libre + combat style DBZ Budokai Tenkaichi (spec Gemini, transmise par Patrick 20/08)

> Source : Patrick a fait produire cette spec par Gemini. À implémenter par étapes,
> en TDD (test de comportement AVANT le code — règle de Patrick). Cible probable :
> le **mode duel / arène** d'abord (voir [[gout-arene-cyberpunk]] et specs-eclairage-duel.md).

## 1. Architecture des systèmes

### Flight & Mana (ex-« Ki » DBZ → chez nous c'est du MANA, univers fantasy)nematics (`PlayerController`)
- Déplacement libre 3D (X, Y, Z), sans gravité en apesanteur (`isFlying`).
- **Dragon Dash** : accélération brusque vers la cible verrouillée, consommation de Mana (ex-« Ki » DBZ → chez nous c'est du MANA, univers fantasy),
  augmentation dynamique du FOV caméra, particules d'aura.

### Lock-On Camera (`TargetCameraSystem`)
- 3e personne (au-dessus de l'épaule), orientée en permanence vers `targetEntity`.
- `cameraPosition = playerPosition + offsetVector` orienté le long de `(targetPosition - playerPosition)`.
- Interpolation `MathUtils.damp` pour amortir + ajuster le zoom selon la distance des combattants.

### State Machine (`CharacterStateMachine`)
- Enum : `IDLE`, `FLYING`, `DRAGON_DASH`, `ATTACKING`, `STUNNED`, `CHARGING_KI`, `SPECIAL_ATTACK`.
- Transitions par booléens : `isGrounded`, `isFlying`, `isLockOnActive`, `isChargingMana (ex-« Ki » DBZ → chez nous c'est du MANA, univers fantasy)`, `hasEnoughMana (ex-« Ki » DBZ → chez nous c'est du MANA, univers fantasy)`.

### Combat & Hitbox Engine (`CombatSystem`)
- Combos légers/lourds via file d'entrées (*input buffering*).
- Impacts par sphères englobantes (`BoundingSphere`) ou raycast sur os d'attaque (`hand_R`, `foot_L`).
- Knockback par vecteurs d'impulsion → `STUNNED`, *hit-stop*, poussière sur collision décor.

### Mana (ex-« Ki » DBZ → chez nous c'est du MANA, univers fantasy) & Projectiles (`Mana (ex-« Ki » DBZ → chez nous c'est du MANA, univers fantasy)System`)
- Recharge Mana (ex-« Ki » DBZ → chez nous c'est du MANA, univers fantasy) en maintenant la touche (`isChargingMana (ex-« Ki » DBZ → chez nous c'est du MANA, univers fantasy) = true`).
- Tirs d'énergie via pooling d'objets (`ObjectPool`) ; rayon (`Kamehameha`) = cylindre déformé par `ShaderMaterial`.

## 2. Conventions de code strictes
- camelCase (vars/fonctions), PascalCase (classes), UPPER_SNAKE_CASE (constantes).
- Booléens préfixés `is`/`has`/`can`.
- 1 fonction = 1 responsabilité (15-20 lignes max).
- Séparation : Présentation (meshes/shaders) / Métier (états/physique) / Données (stats) / Infra (inputs).
- Fail fast, pas d'exception avalée.

## Découpage proposé (à valider avec Patrick, une brique à la fois)
1. **Socle vol libre** : `isFlying`, déplacement X/Y/Z, monter/descendre. (base de tout)
2. **Caméra lock-on** : verrou sur l'adversaire (R existe déjà), caméra épaule + damp.
3. **Dragon Dash** : fonce sur la cible verrouillée + FOV + aura.
4. **Machine à états** : formaliser IDLE/FLYING/DASH/ATTACK/STUN/CHARGE.
5. **Combos** : input buffer, enchaînements légers/lourds, hit-stop + knockback (une partie existe déjà dans frapper()).
6. **Mana (ex-« Ki » DBZ → chez nous c'est du MANA, univers fantasy) & projectiles** : jauge (existe pour le mage), tirs poolés, Kamehameha shader.

Note : le jeu actuel est un dungeon-crawler AU SOL. Le vol libre est une transformation
profonde → on le monte dans l'arène/duel d'abord, sans casser le mode donjon.

## Découpage technique Three.js (2e lot de la spec Gemini)

### Vol et cinématique 3D
- Déplacements en `Vector3`. En mode vol, **linear damping** remplace la friction sol
  (garde l'inertie dans l'air).
- **Dragon Dash** : `direction = targetPos.clone().sub(playerPos).normalize()` puis
  vitesse élevée sur cette trajectoire.

### Caméra orbitale dynamique
- `camera.lookAt(targetPosition)`.
- Position X/Z de la caméra maintenue **derrière le joueur par rapport à l'axe
  joueur→cible** → l'adversaire reste toujours au centre de l'écran.

### Hitboxes & physique des impacts
- Projection : `impulse = direction.multiplyScalar(knockbackForce)` sur la vitesse de l'adverse.
- `Raycaster` orienté vers le bas → distance au sol → bascule auto vol↔marche (`isGrounded`).

### Particules & Shaders (VFX)
- Aura de charge : `Mesh` englobant le perso + `CustomShaderMaterial` animé par uniform `time`.
- Speed lines pendant les dashes : passe de post-processing OU quad-planes transparents
  ancrés devant la caméra.

## Ce qu'on a DÉJÀ dans le jeu (à réutiliser, ne pas réécrire)
- Lock cible = touche **R** (déjà là).
- `frapper()` : combos, knockback, hit-stop (partiellement fait).
- Jauge d'énergie + charge (touche F, mage) → base du Mana (ex-« Ki » DBZ → chez nous c'est du MANA, univers fantasy).
- Projectiles élémentaires.
- Mode arène/entraînement (-1) avec un guerrier adversaire.
