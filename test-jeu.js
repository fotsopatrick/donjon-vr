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
// GARDE-FOU MÉMOIRE DU MONDE (23/08) : une conséquence doit survivre à l'action.
// Le coffre de l'étage 1 est la première pierre : fait noté à l'ouverture, relu
// à la pose du coffre, stocké DANS la sauvegarde joueur (même identité).
v('memoire du monde (faits + noterFait)', /let faits\s*=\s*\{\}/.test(script) && /function noterFait/.test(script) && /function lireFait/.test(script));
v('les faits voyagent DANS la sauvegarde joueur', /pouvoirs,\s*faits\s*\}\)\)/.test(script));
v('faits restaures a la reprise / remis a zero en nouvelle partie', /sv\.faits\s*\|\|\s*\{\}/.test(script) && /niveauMax = 1; faits = \{\};/.test(script));
v('coffre de l\'etage 1 identifie (cle stable)', /'etage'\s*\+\s*niveau\s*\+\s*':coffre'/.test(script));
v('ouverture du coffre note le fait', /poserCoffreOuvert\(coffre\);\s*\n\s*if\(coffre\.id\)\s*noterFait\(coffre\.id,\s*true\)/.test(script));
v('coffre deja ouvert relu a la pose (pas de deuxieme contenu)', /coffre\.id && lireFait\(coffre\.id\)\) poserCoffreOuvert\(coffre\)/.test(script));
v('etat du monde observable par le harnais (window.D.faits)', /get faits\(\)\{ return faits; \}/.test(script));
// On LIT la hauteur au lieu de recopier le chiffre : sinon le contrôle casse
// dès qu'on change le plafond, et il ne vérifie plus rien d'utile.
v('plafond très haut (HT>=8)', (function(){
  const m = script.match(/let HT\s*=\s*([\d.]+)/);
  return !!m && parseFloat(m[1]) >= 8;
})());
v('couloirs elargis (2 cases)', /grid\[y\+1\]\[x\]=FLOOR/.test(script) && /grid\[y\]\[x\+1\]=FLOOR/.test(script));
// GARDE-FOU SALLE D'ENTRAÎNEMENT (Patrick 22/08 : « dégueulasse, trop sombre ») :
// le plateau doit rester ÉCLAIRÉ — projecteur du ring + sol néon vif.
v('salle d\'entrainement eclairee (projecteur du ring)', /projRing\s*=\s*new THREE\.PointLight/.test(script));
v('sol de l\'arene qui brille (emissiveIntensity fort)', /emissiveMap:gt, emissiveIntensity:\s*(?:[2-9]|\d\d)/.test(script));
// GARDE-FOU MUR AU SOL (Patrick 22/08 : « murs invisibles, déplacés vers le haut »).
// La boîte du mur DOIT se refaire quand la hauteur HT change, sinon le mur monte
// sans grandir et son bas décolle du sol → mur invisible en bas.
v('la boite du mur se refait quand la hauteur change', /geoMurH\s*!==\s*HT/.test(script) && /geoMur\s*=\s*new THREE\.BoxGeometry\(T,\s*HT,\s*T\)/.test(script));
// GARDE-FOU CERCLE (Patrick 22/08 : « impossible d'atteindre les cercles ») :
// dans le plan de l'étage 1, le cercle K doit rester PRÈS du départ S (moins de
// 4 cases), sinon il se retrouve caché au fond du labyrinthe et on ne l'atteint plus.
v('cercle de teleportation pres du depart (etage 1)', (function(){
  const m = script.match(/const PLAN_ETAGE1 = \{[^\[]*lignes:\s*\[([\s\S]*?)\n\]\}/);
  if(!m) return false;
  const lignes = [...m[1].matchAll(/"([^"]*)"/g)].map(x=>x[1]);
  let K=null, S=null;
  lignes.forEach((l,y)=>{ for(let x=0;x<l.length;x++){ if(l[x]==='K') K={x,y}; if(l[x]==='S') S={x,y}; } });
  if(!K || !S) return false;
  return (Math.abs(K.x-S.x) + Math.abs(K.y-S.y)) <= 4;
})());
v('avatar par joueur (persoHamda)', /perso-hamda\.glb/.test(script) && /perso.*\+.*joueurNom|'perso' \+ /.test(script));
v('guerrier a defier dans le donjon (poserGuerrier)', /function poserGuerrier/.test(script) && /function majGuerrier/.test(script));
v('touche G pour defier', /KeyG/.test(script));
v('trainee de lame (effet anime au coup)', /trainee/.test(script));
v('auto-baisse de qualite si ca rame (autoFps)', /autoFps/.test(script) && /baisserQualite\(\)/.test(script));
v('combos epee et poings (touche X)', /attaquesEpee/.test(script) && /attaquesPoings/.test(script) && /KeyX/.test(script));
v('projectiles elementaires (feu/eau/vent)', /function lancerProjectile/.test(script) && /'feu'|feu:/.test(script));
v('traduction du chat branchée (TranslationService)', /traduireLeChat/.test(script) && /chat-traduction\.js/.test(html));
v('ligne de traduction japonaise présente', /id="traduction"/.test(html) && /🇯🇵/.test(script));
v('menu pause present', /id="menu-pause"/.test(html));
v('creation de skills (localStorage par joueur)', /kotoage-skills-/.test(script) && /function ouvrirPause/.test(script));
v('incantation feu branchee', /includes\('feu'\)|includes\("feu"\)/.test(script));
v('guerrier arme du meme combat (attaque/hit/mort)', /guerrier[\s\S]{0,40}Sword_Attack|Sword_Attack[\s\S]{0,200}guerrier|EX = \{ Idle_Loop/.test(script) && /guerrier\.jouer/.test(script));
// GARDE-FOU BANQUE (démo 2 min, plan validé 28/08) : la salle existe, la palette
// bleu/gris, le guichet, l'écran de solde, le portail passerelle Azure, et les
// compétences renommées en actions bancaires.
v('banque : salle (batirBanque)', /function batirBanque\(/.test(script));
v('banque : predicat (estBanque niveau -2)', /function estBanque\(\)\{\s*return niveau === -?\d+;\s*\}/.test(script) && /niveau === -2/.test(script));
v('banque : ancre #banque', /h==='arene'\|\|h==='donjon'\|\|h==='village'\|\|h==='banque'/.test(script) && /h==='banque'\?-2/.test(script));
v('banque : palette bleu nuit (fond)', /0x0a1220/.test(script));
v('banque : palette anneaux bleu clair', /0x2f9bff/.test(script) && /0x2f7ed6/.test(script));
v('banque : palette sol emissif bleu', /0x1e6ae0/.test(script));
v('banque : liseré cyan (bandeau guichet)', /0x38c8ff/.test(script));
v('banque : guichet posé', /guichet\s*=\s*new THREE\.Mesh/.test(script));
v('banque : ecran de solde (fabriquerPanneau reutilisé)', /banqueEcran\s*=\s*fabriquerPanneau/.test(script));
v('banque : peintreBanque (redessine la toile)', /function peintreBanque/.test(script));
v('banque : portail posé dans la salle', /poserPortail\(cx,\s*cz\s*-\s*4\)/.test(script));
v('banque : portail -> requete sandbox Azure', /donjon\/sandbox/.test(script) && /action:\x27provision\x27/.test(script));
v('banque : sandbox ne casse pas si la Tour dort (HORS LIGNE)', /\.catch\(\(\)=>peintreBanque\('HORS LIGNE'/.test(script));
v('banque : ecran + statut exposés au harnais (D.banque)', /get banque\(\)\{ return \{ ecran: banqueEcran/.test(script));
v('banque : harnais D exposes estBanque', /get estBanque\(\)\{ return estBanque; \}/.test(script));
v('banque : compétence « Valider un virement » (nom + mot clé)', /Valider un virement/.test(script) && /valider un virement/.test(script));
v('banque : compétence « Approuver un prêt »', /Approuver un prêt/.test(script) && /approuver un prêt/.test(script));
v('banque : compétence « Vérifier antifraude »', /Vérifier antifraude/.test(script));
v('banque : compétence « Audit interne »', /Audit interne/.test(script));
v('banque : compétence « Transfert SWIFT »', /Transfert SWIFT/.test(script));

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
