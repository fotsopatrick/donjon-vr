/* sky-system.js — SYSTÈME DE CIEL (WorldArtDirectionProfile, stylized realism).

Le ciel n'est plus une simple image de fond fixe : il PILOTE la lumière du monde.
Un preset (village_day, village_golden, forest_day, forest_overcast,
dungeon_interior, night_fantasy, magical_sky) fixe d'un coup :

  · la TOILE DE CIEL : un dégradé zénith → horizon, généré à la volée, avec le
    château photographié composé à l'horizon quand le preset le demande ;
  · le soleil (position, couleur, intensité — et la DirectionalLight du jeu) ;
  · la lune et les étoiles (presets de nuit) ;
  · les nuages (taches douces qui dérivent, dans un groupe qui suit la caméra) ;
  · l'hémisphère (ciel/sol) et l'ambiance ;
  · le brouillard (couleur, densité) ;
  · l'exposition du rendu.

La toile est posée en `scene.background` (infinie, toujours derrière le monde :
les montagnes ne sont jamais masquées). Le soleil, la lune et les nuages vivent
dans un groupe qui SUIT la caméra sans sa rotation (la caméra a far=80).

Chaque preset est prêt ; seul le village est branché pour l'instant.
*/
import * as THREE from './three.module.js';

const K = window.KOTOAGE;
if (!K) console.warn('[SKY] KOTOAGE absent — le système de ciel ne s\'accroche pas.');

let _texNuage = null;
function texNuage(){
  if(_texNuage) return _texNuage;
  const S = 128, c = document.createElement('canvas'); c.width = c.height = S;
  const g = c.getContext('2d');
  const d = g.createRadialGradient(S/2, S/2, 4, S/2, S/2, S/2);
  d.addColorStop(0, 'rgba(255,255,255,0.95)');
  d.addColorStop(0.45, 'rgba(255,255,255,0.45)');
  d.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = d; g.fillRect(0, 0, S, S);
  _texNuage = new THREE.CanvasTexture(c);
  return _texNuage;
}

/* le SOLEIL : une source de lumière en dégradé radial, PAS une primitive plate.
   Cœur blanc chaud → jaune doré → halo transparent : aucune arête visible. */
let _texSoleil = null;
function texSoleil(){
  if(_texSoleil) return _texSoleil;
  const S = 256, c = document.createElement('canvas'); c.width = c.height = S;
  const g = c.getContext('2d');
  const d = g.createRadialGradient(S/2, S/2, 0, S/2, S/2, S/2);
  d.addColorStop(0, 'rgba(255,253,242,1)');
  d.addColorStop(0.16, 'rgba(255,246,220,0.96)');
  d.addColorStop(0.38, 'rgba(255,228,168,0.5)');
  d.addColorStop(0.68, 'rgba(255,200,128,0.14)');
  d.addColorStop(1, 'rgba(255,184,96,0)');
  g.fillStyle = d; g.fillRect(0, 0, S, S);
  _texSoleil = new THREE.CanvasTexture(c);
  return _texSoleil;
}

const PRESETS = {
  village_day: {
    skyTop: 0x4a8fd6, skyMid: 0x9ecdf0, skyBottom: 0xd8e8f4,
    soleil: [-0.4, 0.9, 0.5], soleilCouleur: 0xfff3d8, soleilForce: 3.0,
    hemiCiel: 0xfff2dc, hemiSol: 0x9a8a68, hemiForce: 1.5,
    ambiance: 1.4, exposition: 1.15,
    brouillard: 0xcfe4f5, brouillardD: 0.006,
    nuages: 10, nuagesOpacite: 0.8,
    lune: false, etoiles: false, chateau: true,
  },
  village_golden: {
    skyTop: 0x4a7ab0, skyMid: 0xa0b4c8, skyBottom: 0xd6d2c6,
    soleil: [-0.6, 0.62, 0.5], soleilCouleur: 0xffe0b0, soleilForce: 2.35,
    hemiCiel: 0xe8e4e0, hemiSol: 0xb0a488, hemiForce: 2.2,
    ambiance: 1.4, exposition: 1.12,
    brouillard: 0xd6d2c6, brouillardD: 0.007,
    nuages: 8, nuagesOpacite: 0.55,
    lune: false, etoiles: false, chateau: true,
  },
  forest_day: {
    skyTop: 0x3f83c8, skyMid: 0x8fc6ec, skyBottom: 0xcfe6f2,
    soleil: [-0.2, 0.8, 0.6], soleilCouleur: 0xfff0d8, soleilForce: 2.6,
    hemiCiel: 0xdff0f4, hemiSol: 0x6a7a52, hemiForce: 1.9,
    ambiance: 1.2, exposition: 1.12,
    brouillard: 0xcde8ee, brouillardD: 0.010,
    nuages: 12, nuagesOpacite: 0.85,
    lune: false, etoiles: false, chateau: false,
  },
  forest_overcast: {
    skyTop: 0x6a6f78, skyMid: 0x9aa0a8, skyBottom: 0xc6c9cc,
    soleil: [-0.2, 0.5, 0.4], soleilCouleur: 0xdde4ea, soleilForce: 1.3,
    hemiCiel: 0xc8ced4, hemiSol: 0x5a5a50, hemiForce: 1.6,
    ambiance: 1.3, exposition: 1.05,
    brouillard: 0xbcc2c8, brouillardD: 0.016,
    nuages: 16, nuagesOpacite: 0.95,
    lune: false, etoiles: false, chateau: false,
  },
  dungeon_interior: {
    skyTop: 0x1a1a22, skyMid: 0x262633, skyBottom: 0x141418,
    soleil: [0.3, 0.4, 0.2], soleilCouleur: 0x8f9cff, soleilForce: 1.2,
    hemiCiel: 0x6274a0, hemiSol: 0x161c2a, hemiForce: 0.9,
    ambiance: 0.5, exposition: 1.2,
    brouillard: 0x101626, brouillardD: 0.026,
    nuages: 0, nuagesOpacite: 0,
    lune: false, etoiles: false, chateau: false,
  },
  night_fantasy: {
    skyTop: 0x05060f, skyMid: 0x131a3a, skyBottom: 0x2a3050,
    soleil: [-0.7, 0.25, 0.3], soleilCouleur: 0xb0c8ff, soleilForce: 1.1,
    hemiCiel: 0x2a3a6a, hemiSol: 0x141a26, hemiForce: 0.9,
    ambiance: 0.6, exposition: 1.2,
    brouillard: 0x1a2440, brouillardD: 0.012,
    nuages: 5, nuagesOpacite: 0.35,
    lune: true, etoiles: true, chateau: true,
  },
  magical_sky: {
    skyTop: 0x1a1a34, skyMid: 0x3a3a66, skyBottom: 0x7a5a8a,
    soleil: [-0.3, 0.6, 0.5], soleilCouleur: 0xbfe0ff, soleilForce: 2.0,
    hemiCiel: 0x9a7ab0, hemiSol: 0x2a1a30, hemiForce: 1.4,
    ambiance: 0.9, exposition: 1.15,
    brouillard: 0x5a4a6a, brouillardD: 0.010,
    nuages: 6, nuagesOpacite: 0.5,
    lune: true, etoiles: true, chateau: false,
  },
};

let _soleil = null, _lune = null, _etoiles = null, _nuages = null;
let _actif = false, _toileTex = null, _chateauImg = null;

/* ── la toile de ciel : dégradé zénith → horizon, château composé à l'horizon ── */
function _couleur(hex){
  return '#' + new THREE.Color(hex).getHexString();
}
function construireToile(p){
  const W = 1024, H = 512;
  const c = document.createElement('canvas'); c.width = W; c.height = H;
  const g = c.getContext('2d');
  const haut = _couleur(p.skyTop), milieu = _couleur(p.skyMid), bas = _couleur(p.skyBottom);
  // zénith → horizon
  const gr = g.createLinearGradient(0, 0, 0, H);
  gr.addColorStop(0, haut);
  gr.addColorStop(0.5, milieu);
  gr.addColorStop(1, bas);
  g.fillStyle = gr; g.fillRect(0, 0, W, H);
  // le château : décor distant composé au-dessus de l'horizon, SANS couture.
  // La bande est fondue en alpha (transparente en haut et en bas) pour ne
  // laisser AUCUNE rupture horizontale entre le château et le dégradé.
  if(p.chateau && _chateauImg){
    const img = _chateauImg;
    const hh = H * 0.34;                       // hauteur de la bande d'horizon
    const ratio = img.width / img.height;
    let dw = W, dh = dw / ratio;
    if(dh < hh){ dh = hh; dw = dh * ratio; }
    // fondue verticale sur un canvas intermédiaire
    const tmp = document.createElement('canvas');
    tmp.width = W; tmp.height = hh;
    const tg = tmp.getContext('2d');
    tg.drawImage(img, (W - dw) / 2, (hh - dh) / 2, dw, dh);
    const fade = tg.createLinearGradient(0, 0, 0, hh);
    fade.addColorStop(0, 'rgba(0,0,0,0)');
    fade.addColorStop(0.22, 'rgba(0,0,0,1)');
    fade.addColorStop(0.78, 'rgba(0,0,0,1)');
    fade.addColorStop(1, 'rgba(0,0,0,0)');
    tg.globalCompositeOperation = 'destination-in';
    tg.fillStyle = fade; tg.fillRect(0, 0, W, hh);
    // posée juste sous la ligne d'horizon
    const dy = H * 0.5 - hh * 0.42;
    g.globalAlpha = 0.92;
    g.drawImage(tmp, 0, dy);
    g.globalAlpha = 1;
  }
  _toileTex = new THREE.CanvasTexture(c);
  _toileTex.colorSpace = THREE.SRGBColorSpace;
  return _toileTex;
}

function groupeCiel(){
  const groupe = new THREE.Group();
  groupe.name = 'sky-groupe';

  /* soleil : une source en dégradé radial (pas une primitive plate) */
  _soleil = new THREE.Group();
  const disque = new THREE.Sprite(new THREE.SpriteMaterial({
    map: texSoleil(), color: 0xfff4dc, transparent: true, depthWrite: false,
    fog: false, toneMapped: false }));
  disque.scale.setScalar(48);
  _soleil.add(disque);
  groupe.add(_soleil);

  /* lune */
  _lune = new THREE.Group();
  _lune.add(new THREE.Mesh(
    new THREE.CircleGeometry(5.5, 28),
    new THREE.MeshBasicMaterial({ color: 0xcfe0ff, fog: false, toneMapped: false })));
  _lune.add(new THREE.Sprite(new THREE.SpriteMaterial({
    map: texNuage(), color: 0x9ab8e8, transparent: true, opacity: 0.26,
    blending: THREE.AdditiveBlending, depthWrite: false })));
  _lune.children[1].scale.setScalar(70);
  _lune.visible = false;
  groupe.add(_lune);

  /* étoiles */
  const N = 220, pos = new Float32Array(N * 3);
  for(let i = 0; i < N; i++){
    const a = Math.random() * Math.PI * 2;
    const h = Math.PI / 2 * (0.15 + Math.random() * 0.85);
    pos[i*3]   = Math.cos(a) * Math.cos(h) * 70;
    pos[i*3+1] = Math.sin(h) * 70;
    pos[i*3+2] = Math.sin(a) * Math.cos(h) * 70;
  }
  _etoiles = new THREE.Points(
    new THREE.BufferGeometry().setAttribute('position', new THREE.BufferAttribute(pos, 3)),
    new THREE.PointsMaterial({ color: 0xdfe8ff, size: 1.4, sizeAttenuation: false,
      transparent: true, opacity: 0.0, depthWrite: false, fog: false }));
  groupe.add(_etoiles);

  /* nuages : taches douces qui dérivent */
  _nuages = new THREE.Group();
  const geoNu = new THREE.PlaneGeometry(52, 15);
  const matNu = new THREE.MeshBasicMaterial({
    map: texNuage(), transparent: true, depthWrite: false, fog: false,
    side: THREE.DoubleSide, opacity: 0.6 });
  for(let i = 0; i < 16; i++){
    const n = new THREE.Mesh(geoNu, matNu.clone());
    n.userData = {
      a: Math.random() * Math.PI * 2,
      d: 40 + Math.random() * 22,
      h: 26 + Math.random() * 26,
      v: 0.6 + Math.random() * 0.8,
      ech: 0.7 + Math.random() * 1.3,
      ph: Math.random() * 6,
    };
    n.scale.set(n.userData.ech, 1, 1);
    _nuages.add(n);
  }
  groupe.add(_nuages);

  K.scene.add(groupe);
  return groupe;
}
let _groupe = null;

function majPositions(p){
  const dir = new THREE.Vector3(p.soleil[0], p.soleil[1], p.soleil[2]).normalize();
  if(_soleil){
    _soleil.position.copy(dir).multiplyScalar(66);
    _soleil.lookAt(0, 0, 0);
    if(_soleil.children[0]) _soleil.children[0].material.color.setHex(p.soleilCouleur);
    _soleil.visible = true;
  }
  if(_lune){
    _lune.visible = p.lune;
    if(p.lune){
      const d = new THREE.Vector3(-p.soleil[0], p.soleil[1] * 0.85, -p.soleil[2]).normalize();
      _lune.position.copy(d).multiplyScalar(66);
      _lune.lookAt(0, 0, 0);
    }
  }
  if(_etoiles) _etoiles.visible = p.etoiles;
  if(_nuages){
    const n = p.nuages;
    for(let i = 0; i < _nuages.children.length; i++){
      const c = _nuages.children[i];
      c.visible = i < n;
      c.material.opacity = c.visible ? p.nuagesOpacite * 0.85 : 0;
    }
  }
}

function appliquer(nom){
  const p = PRESETS[nom] || PRESETS.village_day;
  if(!_groupe) _groupe = groupeCiel();

  // la toile de ciel (dégradé + château à l'horizon) : infinie, jamais devant le monde
  _toileTex = construireToile(p);
  K.scene.background = _toileTex;

  if(K.jour){
    K.jour.position.set(p.soleil[0], p.soleil[1], p.soleil[2]);
    K.jour.intensity = p.soleilForce;
    K.jour.color.setHex(p.soleilCouleur);
    K.jour.castShadow = true;
  }
  if(K.hemi){
    K.hemi.color.setHex(p.hemiCiel);
    K.hemi.groundColor.setHex(p.hemiSol);
    K.hemi.intensity = p.hemiForce;
  }
  if(K.ambiance) K.ambiance.intensity = p.ambiance;
  if(K.renderer) K.renderer.toneMappingExposure = p.exposition;
  K.scene.fog = new THREE.FogExp2(p.brouillard, p.brouillardD);

  majPositions(p);
  _actif = true;
  window.SKY_actif = true;
  return p;
}

// on récupère l'image du château (le décor distant) depuis KOTOAGE quand elle est prête
(function chargerChateau(){
  if(!K || !K.photoFond) return;
  const img = K.photoFond().image;
  if(img && img.width){ _chateauImg = img; return; }
  setTimeout(chargerChateau, 400);
})();

let _dtPrec = 0;
function _boucle(t){
  const dt = _dtPrec ? Math.min(0.05, (t - _dtPrec) / 1000) : 0;
  _dtPrec = t;
  if(_actif){
    if(_groupe && K.camera) _groupe.position.copy(K.camera.position);
    if(_nuages){
      const now = t / 1000;
      for(const c of _nuages.children){
        if(!c.visible) continue;
        const u = c.userData;
        u.a += dt * u.v * 0.002;
        c.position.set(Math.cos(u.a) * u.d, u.h + Math.sin(now * 0.12 + u.ph) * 2.2, Math.sin(u.a) * u.d);
        c.lookAt(0, 0, 0);
      }
    }
  }
  requestAnimationFrame(_boucle);
}
requestAnimationFrame(_boucle);

window.SKY = { appliquer, presets: Object.keys(PRESETS), actif: () => _actif };
