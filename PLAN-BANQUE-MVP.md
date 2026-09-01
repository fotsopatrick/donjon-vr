# PLAN-BANQUE-MVP — simulateur bancaire 3D dans Kotoage

> **Objectif** : transformer une salle 3D du Donjon en **simulateur bancaire**
> pour une démo de 2 minutes dans un entretien Platform Engineer.
> Durée cible : < 2 h. Réversible (backup). Utilise 100 % de l'existant.
>
> Validé par Patrick le 28/08/2026 · Statut : **en attente d'exécution**

---

## 1. Rappel : le code existant (vérifié, 28/08/2026)

Jeu = un seul fichier : `~/donjon-vr/index.html` (7343 lignes, Three.js r169
local, zéro réseau sauf 2 appels déjà câblés vers `127.0.0.1:8002`).

| Élément | Où | Rôle pour la banque |
|---|---|---|
| Salle « arène » niveau −1 | `batirArene()` `index.html:3864` | **Base** : salle ouverte, sol TRON, anneaux, piliers, skyline. Entrée directe par l'ancre `#arene` (`:4136`). |
| Thèmes d'étage | `ETAGES[]` `:453` | Sol/plafond/brouillard par niveau → on prend le principe de l'arène, on recolore. |
| Portail de téléportation | `poserPortail()` `:2040`, `lancerTeleport()` `:2060`, `majPortail()` `:2066` | Réutilisable tel quel. Se déclenche à < 1 m du joueur. |
| Compétences | `INCANTATIONS[]` `:4421`, `lancerProjectile(type)` `:5345`, skills perso `:7147-7167`, HUD pouvoirs `:4406` | Renommer la table. Le projectile eau est déjà un « trait bleu » : parfait pour « valider un virement ». |
| Panneau 3D dynamique | `fabriquerPanneau()` `:4898` + `fondIsekai()` `:4916` | Toile canvas collée sur un plan 3D, redessinée quand `tex.needsUpdate=true`. Écran de solde. |
| Appels HTTP | `ALICE_API` `:7174`, `RAPPORT_URL` `:7226` | Motif fetch→POST→JSON→`.catch()` qui ne casse jamais le jeu. |

**Studio** : `~/studio/` (éditeur d'agencement, port 8778) et
`~/donjon-vr/world_builder/` (génération GLB par prompt). ⚠️ Le Studio
**n'est pas branché au jeu** (son `scenes/*.json` ≠ `monde/scene.json` du jeu).
→ Le MVP ci-dessous n'en dépend pas. Transformable plus tard en agence
« vraie » (voir §6 « Étapes suivantes »).

---

## 2. Stratégie

**Ne pas toucher au donjon.** Cloner l'arène en `batirBanque()`, la recolorer
bleu/gris, ajouter un guichet, une enseigne, un écran de solde dynamique et un
portail « passerelle Azure ». Le jeu d'origine reste intact → retour arrière =
`cp index.html.bak-banque index.html`.

---

## 3. Exécution pas à pas

### Étape 0 — Filet de sécurité

```bash
cd ~/donjon-vr
cp index.html index.html.bak-banque        # retour arrière garanti
git stash && git status                    # vérifier que le dépôt est propre
```

### Étape 1 — Nouvelle salle `#banque`

1. Copier `batirArene()` (bloc `:3864-3943`) dans une nouvelle fonction
   `batirBanque()`, SANS `poserGuerrier()` (pas d'entraîneur en banque).
   Le bloc de nettoyage `:3865-3869` (vider `monde`, remettre les tableaux)
   est conservé.
2. **Pointer la copie vers la webapp du studio** SANS appliquer aux deux :
   on recolore la COPIE, pas l'original.
3. Palette banque (remplacements à faire uniquement dans `batirBanque`) :

```bash
sed -i \
 -e 's/scene.background = new THREE.Color(0x060814);/scene.background = new THREE.Color(0x0a1220);/' \
 -e 's/new THREE.FogExp2(0x0a0a1e, 0.019)/new THREE.FogExp2(0x10182a, 0.019)/' \
 -e 's/color:0x0e1428, roughness:0.28, metalness:0.75,/color:0x14203a, roughness:0.35, metalness:0.65,/' \
 -e 's/emissive:0x1a4a8a, emissiveMap:gt, emissiveIntensity:2.4/emissive:0x1e6ae0, emissiveMap:gt, emissiveIntensity:2.2/' \
 -e 's/0x1cf0ff, 0.9\], \[7.2, 0xff2bd6, 0.55/0x2f9bff, 0.9], [7.2, 0x2f7ed6, 0.55/' \
 -e 's/0x1cf0ff, transparent:true, opacity:0.95/0x2f9bff, transparent:true, opacity:0.95/' \
 -e 's/0xff2bd6, transparent:true, opacity:0.5/0x2f7ed6, transparent:true, opacity:0.5/' \
 -e 's/color:0xff3ac0, transparent:true, opacity:0.55/color:0x38b0ff, transparent:true, opacity:0.55/' \
 -e 's/const l1 = new THREE.PointLight(0x1cf0ff/const l1 = new THREE.PointLight(0x2f9bff/' \
 -e 's/const l2 = new THREE.PointLight(0xff2bd6/const l2 = new THREE.PointLight(0x2f7ed6/' \
 index.html
```
⚠️ On applique le sed **au bloc copié seulement** (délimiter par marqueurs de
début/fin pendant la copie, puis retirer les marqueurs après sed).

4. Prédicat + branche dans `nouvelEtage()` (avant `if(estArene())`, `:3957`) :

```js
function estBanque(){ return niveau === -2; }          // à côté de estArene() :472

if(estBanque()){
  batirBanque();
  joueur.x = W*T*0.5 - 5; joueur.z = H*T*0.5;
  joueur.lacet = -Math.PI/2; joueur.tangage = 0;
  joueur.vie = joueur.vieMax; joueur.cle = true;
  elCle.classList.remove('ok'); elEtage.textContent = 'Banque — sandbox Azure';
  dire('Simulateur bancaire. Parle : valider un virement, approuver un prêt.', 6);
  return;
}
```

5. Ancre d'autostart (`:4137`) :

```js
if(h==='arene'||h==='donjon'||h==='village'||h==='banque'){
  departNiveau = h==='arene'?-1 : h==='banque'?-2 : h==='donjon'?1 : 0;
```

### Étape 2 — Le mobilier qui fait « banque » (fin de `batirBanque`)

```js
// guichet : 2 blocs bleu foncé + un liseré lumineux
const guichet = new THREE.Mesh(new THREE.BoxGeometry(T*8, 1.1, 0.5),
  new THREE.MeshStandardMaterial({ color:0x1a2a4a, roughness:0.4, metalness:0.5 }));
guichet.position.set(cx - 4, 1.1/2, cz + 6); monde.add(guichet);
const bandeau = new THREE.Mesh(new THREE.BoxGeometry(T*8.1, 0.15, 0.62),
  new THREE.MeshBasicMaterial({ color:0x38c8ff }));
bandeau.position.set(cx - 4, 1.22, cz + 6); monde.add(bandeau);
```

### Étape 3 — Écran de solde + enseigne

Réutilise `fabriquerPanneau` / `fondIsekai`. Ajouter après `batirBanque` :

```js
const banqueEcran = fabriquerPanneau(700, 400, 2.2);
banqueEcran.mesh.position.set(cx - 6, 3, cz - 12); banqueEcran.mesh.lookAt(cx, 3, cz);
banqueEcran.mesh.visible = false;          // rendu visible uniquement en banque

function peintreBanque(statut, solde){
  const { g, c, tex } = banqueEcran, w = c.width, h = c.height;
  fondIsekai(g, w, h, '30,120,230');
  const ligne = (y, txt, col='#dcefff', size=30) => { g.font=size+'px Georgia, serif';
    g.fillStyle=col; g.textBaseline='top'; g.fillText(txt, 44, y); };
  ligne(40,  'BANQUE CENTRALE — CONSOLE');
  ligne(120, 'Compte n° 3173',               '#8fc4ff', 24);
  ligne(170, 'Solde',                        '#8fc4ff', 24);
  ligne(170, solde,                          '#eaffff', 30);
  ligne(240, 'Sandbox Azure',                '#8fc4ff', 24);
  ligne(240, statut, statut.startsWith('DÉM') ? '#ffd08a' : '#a9ffc8', 26);
  tex.needsUpdate = true;
}
```

Dans la branche `estBanque()` de `nouvelEtage()` : `banqueEcran.mesh.visible = true;`

### Étape 4 — Renommer les compétences

```bash
sed -i \
 -e 's/nom:\x27Boule de Feu\x27/nom:\x27Valider un virement\x27/' \
 -e 's/nom:\x27Flèche de Glace\x27/nom:\x27Approuver un prêt\x27/' \
 -e 's/nom:\x27Lame de Vent\x27/nom:\x27Vérifier antifraude\x27/' \
 -e 's/nom:\x27Ra Tilt\x27/nom:\x27Audit interne\x27/' \
 -e 's/nom:\x27Dragon Slave\x27/nom:\x27Transfert SWIFT\x27/' \
 index.html
```

(`~/.studio/catalogue` : les `cles` restent — on peut encore dire « vent »,
« eau »… Les chants Slayers sont conservés, la voix clonée ne casse pas.)

### Étape 5 — Le portail « passerelle Azure »

Dans `batirBanque`, poser le portail : `poserPortail(cx, cz - 4);`
(les mêmes variables que l'arène : `cx, cz`).

Puis, en tête de `lancerTeleport()` (`:2060`), ajouter le cas banque — qui a
la priorité sur le `descendre()` normal :

```js
function lancerTeleport(){
  if(estBanque()){
    if(teleportT > 0) return;
    teleportT = 1.0;
    peintreBanque('DÉMARRAGE…', '…');                 // l'écran s'allume
    fetch('http://127.0.0.1:8002/donjon/sandbox',
      { method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({ action:'provision' }) })
      .then(r => r.json()).then(d => peintreBanque('ACTIVE ✓  ' + (d.nom||''), '12 400,00 €'))
      .catch(() => peintreBanque('HORS LIGNE', '—')); // jamais de plantage si la Tour dort
    return;
  }
  if(teleportT>0) return;
  // … suite inchangée du donjon
}
```

> Même motif que `ALICE_API` (`:7208`). Aucune nouvelle infrastructure :
> on pointe le port `:8002` existant. Le jour où la Tour expose sa sandbox
> là-dessus, la démo affiche les vrais statuts sans toucher au code.

---

## 4. Valve de vérification/plan de test

```bash
cd ~/donjon-vr
node test-jeu.js                    # 1. syntaxe + invariants inchangés
python3 serveur-nocache.py &        # 2. serveur sans cache (le cache Chrome ment)
# 3. Chrome → http://127.0.0.1:8099/index.html#banque  puis Ctrl+Shift+R
#    VÉRIFIER : salle bleu/gris, enseigne « BANQUE CENTRALE », portail allumé
# 4. V (parler) → « valider un virement » → projectile bleu + message
# 5. Marcher sur le portail → « Téléportation… » → l'écran bascule
#    DÉMARRAGE → ACTIVE (et la requête POST part, à voir dans les logs :8002)
# 6. Stabilité : i/s en haut à droite, sur un VRAI écran → stable (salle =
#    l'arène, déjà légère). Le ThinkCentre (8 Go) doit encaisser sans broncher.
pkill -9 -f "user-data-dir=/tmp/chrome-"    # fermer TOUT chrome de test aussitôt
# 7. git diff -- index.html  → ne doit montrer QUE les ajouts banque
```

Cellule de conformité du projet (CLAUDE.md) : une seule machine à la fois,
un seul chrome de test, jamais le profil de Patrick, le jeu reste local.

---

## 5. Note sécurité / gouvernance (pour l'article)

Ce plan n'introduit **aucune faille nouvelle** :

- Les appels HTTP reutilisent le motif existant (`fetch` POST + `.catch`),
  déjà présent pour Alice (`ALICE_API`, `:7208`) et la carte vivante
  (`RAPPORT_URL`, `:7226`).
- Le portail ne fait que **déclencher une requête** (provision d'une sandbox) :
  pas d'exécution de commande, pas de shell, pas d'infusion de données
  serveur dans le jeu au-delà d'un texte affiché sur un canvas.
- Tout reste **local** (port 127.0.0.1:8002). Le jeu ne va pas sur Internet ;
  seul le dépôt git va sur la tour, comme toujours.
- Réversibilité garantie : `index.html.bak-banque` + les ajouts sont isolés
  dans des nouvelles fonctions ✓ (l'original `batirArene` n'est pas touché).

## 6. Étapes suivantes (après validation de la démo)

- **Agence « vraie » dans le Studio** : dessiner l'agence dans
  `~/studio/donjon-plan.html` (scenes/banque.json : tables → guichet,
  armoire/coffre → coffre-fort), exporter puis **convertir** en
  `monde/scene.json` (le format que `world-builder.js` charge) pour que le
  jeu l'affiche — petit pont à écrire.
- **Génération GLB** d'un comptoir/distributeur par prompt (AI World Builder,
  Blender local) puis placement via la touche B (mode constructeur).
- **Vraie API Azure** derrière `:8002/donjon/sandbox` pour la démo finale.