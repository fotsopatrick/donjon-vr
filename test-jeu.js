// TEST DE NON-RÉGRESSION DU JEU — à lancer AVANT et APRÈS chaque modif.
// But : attraper ce qu'une édition du gros index.html casse en douce.
// Il vérifie 3 choses : (1) la syntaxe du script, (2) les invariants présents
// (fonctions/features qui doivent exister), (3) la physique du saut.

const fs = require('fs');
const cp = require('child_process');

let ok = 0, ko = 0;
const v = (nom, cond) => { if (cond) { ok++; } else { ko++; console.log('  ✗ ' + nom); } };

const html = fs.readFileSync(__dirname + '/index.html', 'utf8');
const script = html.split('<script type="module">')[1].split('</script>')[0];

// 1. SYNTAXE — le script parse (imports neutralisés)
const neutre = script
  .replace(/^import \* as THREE.*/m, 'const THREE={};')
  .replace(/^import \{ GLTFLoader \}.*/m, 'const GLTFLoader=class{};')
  .replace(/^import \{ mergeGeometries \}.*/m, 'const mergeGeometries=()=>{};')
  .replace(/^import \{ RGBELoader \}.*/m, 'const RGBELoader=class{};');
fs.writeFileSync('/tmp/_verifjeu.mjs', neutre);
try { cp.execSync('node --check /tmp/_verifjeu.mjs', {stdio:'pipe'}); v('syntaxe du script', true); }
catch (e) { v('syntaxe du script', false); console.log('    ' + String(e.stderr||e).split('\n')[0]); }

// 2. INVARIANTS — les briques qui doivent rester
const doit = [
  ['la boucle de rendu',        /renderer\.setAnimationLoop\(boucle\)/],
  ['l esprit du donjon',        /function traiterChat\(/],
  ['la reconnaissance vocale',  /SpeechRecognition/],
  ['le gardien de palier',      /function creerBoss\(/],
  ['les 5 etages',              /const ETAGES = \[/],
  ['le village (12 maisons)',   /const MAISONS = \[/],
  ['la fenetre de statut',      /function dessinerStatut\(/],
  ['la vue exterieure (F)',     /function basculerVue\(/],
  ['le ciel photographie',      /chargerCiel/],
  ['les modeles Kenney',        /function chargerModeles\(/],
  ['le SAUT (Espace)',          /joueur\.vy = 5\.2/],
  ['le FONCER (clic droit)',    /contextmenu.*foncer|addEventListener\('contextmenu', ev=>\{ ev\.preventDefault\(\); foncer\(\)/],
  
  ['le RADAR (dessin)',         /function dessinerRadar\(/],
  ['le RADAR appele dans la boucle', /dessinerRadar\(\)/],
  ['la surface de debogage D',  /window\.D = \{/],
  ['avatar Ranger Quaternius par défaut', /Male_Ranger\.gltf/],
  ['avatar animé par un mixer',          /new THREE\.AnimationMixer/],
];
for (const [nom, re] of doit) v('présent : ' + nom, re.test(script));
// invariants côté HTML (pas le script)
v('présent : le RADAR (canvas)', /id="radar"/.test(html));
v('avatar : plus de membres-boîtes animés (u.jambeG)', !/u\.jambeG\.rotation/.test(script));
v('course sur Shift', /ShiftLeft/.test(script));
v('indice souris présent', /[Cc]lique.*regarder|regarder autour/.test(script));
v('avatar joueur = VRM VRoid (persoCustom)', /persoCustom:\s*'assets\/vrm\/[^']+\.vrm'/.test(script));
v('animations normalisées (canonAnim)', /function canonAnim/.test(script));
v('montagnes lointaines (silhouette Skyrim)', /function poserMontagnes/.test(script));
v('avatar orienté vers la marche (VRM/Mixamo demi-tour)', /\(estVRM \|\| estMixamo\) \? Math\.PI : 0/.test(script));
v('support VRM (three-vrm branché)', /VRMLoaderPlugin/.test(script) && /loader\.register/.test(script));
v('sons branchés (sons.js inclus)', /assets\/sons\.js/.test(html));
v('son de coup câblé', /Sons\?\.coup\(\)/.test(script));
v('son de pas câblé', /Sons\?\.pas\(\)/.test(script));
v('salles thématiques (meublerSalle)', /function meublerSalle/.test(script));
v('thèmes assignés aux salles', /r\.theme\s*=/.test(script));
v('salles meublées dans batir', /meublerSalle\(/.test(script));
v('arme tenue en main (os RightHand)', /RightHand/.test(script));
v('arme en main visible en 3e personne', /epeeMain/.test(script));
v('le corps bouge au combat (elanCombat)', /elanCombat/.test(script));
v('frappe sur le squelette (bras droit)', /RightArm\$/.test(script) && /brasD/.test(script));
v('reglage de la frappe (reglerFrappe)', /reglerFrappe/.test(script));
v('personnage anime (Sword_Attack via animSuper)', /Sword_Attack/.test(script) && /animSuper/.test(script));
v('anim attaque jouee a la frappe (jouerAttaque)', /function jouerAttaque/.test(script));
v('attaque calee au rythme du combo (fluide)', /timeScale/.test(script));
v('reglage epee en direct (reglerEpee)', /reglerEpee/.test(script));
v('sauvegarde de partie (localStorage)', /localStorage/.test(script) && /function sauvegarderPartie/.test(script));
v('reprise auto au demarrage', /chargerPartie\(\)/.test(script));
v('choix de joueur Patrick/Hamda', /choix-joueur/.test(html) && /Hamda/.test(html));
v('sauvegarde par joueur (cle nommee)', /'kotoage:'/.test(script));
// On LIT la hauteur au lieu de recopier le chiffre : sinon le contrôle casse
// dès qu'on change le plafond, et il ne vérifie plus rien d'utile.
v('plafond très haut (HT>=8)', (function(){
  const m = script.match(/let HT\s*=\s*([\d.]+)/);
  return !!m && parseFloat(m[1]) >= 8;
})());
v('couloirs elargis (2 cases)', /grid\[y\+1\]\[x\]=FLOOR/.test(script) && /grid\[y\]\[x\+1\]=FLOOR/.test(script));
v('avatar par joueur (persoHamda)', /perso-hamda\.glb/.test(script) && /perso.*\+.*joueurNom|'perso' \+ /.test(script));
v('guerrier a defier dans le donjon (poserGuerrier)', /function poserGuerrier/.test(script) && /function majGuerrier/.test(script));
v('touche G pour defier', /KeyG/.test(script));
v('trainee de lame (effet anime au coup)', /trainee/.test(script));
v('auto-baisse de qualite si ca rame (autoFps)', /autoFps/.test(script) && /baisserQualite\(\)/.test(script));
v('combos epee et poings (touche X)', /attaquesEpee/.test(script) && /attaquesPoings/.test(script) && /KeyX/.test(script));
v('projectiles elementaires (feu/eau/vent)', /function lancerProjectile/.test(script) && /'feu'|feu:/.test(script));
v('menu pause present', /id="menu-pause"/.test(html));
v('creation de skills (localStorage par joueur)', /kotoage-skills-/.test(script) && /function ouvrirPause/.test(script));
v('incantation feu branchee', /includes\('feu'\)|includes\("feu"\)/.test(script));
v('guerrier arme du meme combat (attaque/hit/mort)', /guerrier[\s\S]{0,40}Sword_Attack|Sword_Attack[\s\S]{0,200}guerrier|EX = \{ Idle_Loop/.test(script) && /guerrier\.jouer/.test(script));

// 3. PHYSIQUE DU SAUT — l arc doit monter puis retomber (pic ~0.9 m, ~0.7 s)
{
  let saut=0, vy=5.2, dt=1/60, pic=0, tSol=0, t=0;
  for (let i=0;i<200;i++){
    if (vy!==0 || saut>0){ saut+=vy*dt; vy-=15*dt; if(saut<=0){saut=0;vy=0;tSol=t;} }
    pic=Math.max(pic,saut); t+=dt; if(saut===0 && i>2) break;
  }
  v('saut : pic entre 0.7 et 1.2 m', pic>0.7 && pic<1.2);
  v('saut : retombe (durée 0.4–1.0 s)', tSol>0.4 && tSol<1.0);
}

console.log(`\n  ${ok} réussis, ${ko} échoués`);
process.exit(ko === 0 ? 0 : 1);
