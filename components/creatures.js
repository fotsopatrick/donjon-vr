/* components/creatures.js — BIBLIOTHÈQUE DE CRÉATURES RÉUTILISABLES
   (Projet A — Donjon VR, chantier créatures ; prévue pour le Projet B Studio).

   Chaque entrée du REGISTRE est un COMPOSANT stable :
     componentId, version, category, type (relié au gameplay), scale, anchor,
     hauteurBarre, ombre, qualite (L2-L5), materials, animation, metadata.

   Règles :
   - l'ancrage est au SOL (pivot du groupe à y=0) — les créatures ne flottent pas ;
   - les géométries et matériaux sont PARTAGÉS entre instances (perf) ; seuls
     les matériaux animés (opacité du spectre) sont clonés par instance ;
   - `userData.corps` désigne le mesh animé par la boucle du jeu (pulse, brûlure) ;
   - une animation d'idle (queue, voile) tourne dans ce module, pas dans index.html.

   Les composants sont instanciables plusieurs fois et référençables par la
   future webapp 2D du Studio via `CREATURES.liste()`.
*/
import * as THREE from '../three.module.js';

let _texDouce = null;
function texDouce(){
  if(_texDouce) return _texDouce;
  const S = 64, c = document.createElement('canvas'); c.width = c.height = S;
  const g = c.getContext('2d');
  const d = g.createRadialGradient(S/2, S/2, 2, S/2, S/2, S/2);
  d.addColorStop(0, 'rgba(255,255,255,0.9)');
  d.addColorStop(0.5, 'rgba(255,255,255,0.35)');
  d.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = d; g.fillRect(0, 0, S, S);
  _texDouce = new THREE.CanvasTexture(c);
  return _texDouce;
}

/* ─────────────────────────── LE RAT ───────────────────────────
   Volume : corps, tête, museau, oreilles, quatre pattes, queue. Il court au
   ras du sol, l'idle fait fouetter la queue. Matière brune rugueuse. */
function construireRat(opts){
  const L2 = opts.qualite === 'L2';
  const seg = L2 ? 7 : 12;
  const geo = {
    corps:   new THREE.SphereGeometry(0.34, seg, Math.max(6, seg - 2)),
    tete:    new THREE.SphereGeometry(0.17, seg, Math.max(6, seg - 2)),
    museau:  new THREE.SphereGeometry(0.09, 8, 6),
    oreille: new THREE.SphereGeometry(0.07, 7, 5),
    patte:   new THREE.CylinderGeometry(0.028, 0.02, 0.11, 6),
    queue:   new THREE.CylinderGeometry(0.032, 0.008, 0.5, 6),
    oeil:    new THREE.SphereGeometry(0.032, 6, 5),
    blob:    new THREE.CircleGeometry(0.4, 18),
  };
  const matPelage = new THREE.MeshStandardMaterial({ color:0x84725f, roughness:0.95, metalness:0 });
  const matOeil   = new THREE.MeshBasicMaterial({ color:0xff2a1a });
  const matBlob   = new THREE.MeshBasicMaterial({ color:0x000000, transparent:true, opacity:0.16, depthWrite:false });
  const g = new THREE.Group();

  const corps = new THREE.Mesh(geo.corps, matPelage);
  corps.scale.set(1, 0.66, 1.5); corps.position.set(0, 0.26, 0);
  corps.castShadow = true; corps.receiveShadow = false;
  g.add(corps);

  const tete = new THREE.Mesh(geo.tete, matPelage);
  tete.scale.set(1, 0.92, 0.95); tete.position.set(0, 0.34, 0.4);
  tete.castShadow = true; tete.receiveShadow = false;
  g.add(tete);

  const museau = new THREE.Mesh(geo.museau, matPelage);
  museau.scale.set(1, 0.7, 1.45); museau.position.set(0, 0.3, 0.58);
  museau.castShadow = true; museau.receiveShadow = false;
  g.add(museau);

  for(const c of [-1, 1]){
    const or = new THREE.Mesh(geo.oreille, matPelage);
    or.scale.set(1, 1.7, 0.5); or.position.set(c*0.13, 0.52, 0.32);
    or.rotation.z = c*0.32; or.castShadow = true; or.receiveShadow = false;
    g.add(or);
    const o = new THREE.Mesh(geo.oeil, matOeil);
    o.position.set(c*0.09, 0.36, 0.52);
    g.add(o);
  }
  for(const c of [-1, 1]) for(const d of [-1, 1]){
    const p = new THREE.Mesh(geo.patte, matPelage);
    p.position.set(c*0.17, 0.055, d*0.33);
    p.castShadow = true; p.receiveShadow = false;
    g.add(p);
  }
  const queue = new THREE.Mesh(geo.queue, matPelage);
  queue.position.set(0, 0.16, -0.44); queue.rotation.x = Math.PI/2.5;
  queue.castShadow = true; queue.receiveShadow = false;
  g.add(queue);

  const blob = new THREE.Mesh(geo.blob, matBlob);
  blob.rotation.x = -Math.PI/2; blob.position.set(0, 0.02, 0);
  g.add(blob);

  g.userData.corps = corps;
  g.userData._anim = { queue, ph: opts.ph || 0 };
  return g;
}

/* ─────────────────────────── LE SPECTRE ───────────────────────────
   Volume 3D crédible : deux couches de robe (dont une qui tourne), tête,
   bras de brume, yeux luisants, halo doux. Il flotte, mais la robe est un
   vrai volume. L'opacité de la robe est animée par la boucle du jeu (pulse). */
function construireSpectre(opts){
  const L2 = opts.qualite === 'L2';
  const seg = L2 ? 8 : 14;
  const geo = {
    robe: new THREE.CylinderGeometry(0.34, 0.52, 1.4, seg, 3, true),
    robe2: new THREE.CylinderGeometry(0.26, 0.42, 1.25, seg, 2, true),
    tete: new THREE.SphereGeometry(0.17, seg, Math.max(7, seg - 3)),
    bras: new THREE.ConeGeometry(0.08, 0.62, 7),
    oeil: new THREE.SphereGeometry(0.05, 8, 7),
    blob: new THREE.CircleGeometry(0.5, 18),
  };
  const matRobe = new THREE.MeshStandardMaterial({
    color:0xb8a0e8, emissive:0x7a3fd0, emissiveIntensity:1.1,
    transparent:true, opacity:0.5, roughness:0.35,
    side:THREE.DoubleSide, depthWrite:false });
  const matOeil = new THREE.MeshBasicMaterial({ color:0xffd6ff });
  const matBlob = new THREE.MeshBasicMaterial({ color:0x1a1030, transparent:true, opacity:0.25, depthWrite:false });
  const g = new THREE.Group();

  const robe = new THREE.Mesh(geo.robe, matRobe);
  robe.position.y = 0.7;
  robe.castShadow = false; robe.receiveShadow = false;
  g.add(robe);
  const robe2 = new THREE.Mesh(geo.robe2, matRobe);
  robe2.position.y = 0.68; robe2.rotation.y = Math.PI/4;
  robe2.castShadow = false; robe2.receiveShadow = false;
  g.add(robe2);
  const tete = new THREE.Mesh(geo.tete, matRobe);
  tete.position.y = 1.5; tete.scale.set(1, 1.15, 1);
  g.add(tete);
  for(const c of [-1, 1]){
    const b = new THREE.Mesh(geo.bras, matRobe);
    b.position.set(c*0.3, 0.95, 0); b.rotation.z = c*0.9;
    g.add(b);
  }
  for(const c of [-1, 1]){
    const o = new THREE.Mesh(geo.oeil, matOeil);
    o.position.set(c*0.07, 1.56, 0.15);
    g.add(o);
  }
  const halo = new THREE.Sprite(new THREE.SpriteMaterial({
    map:texDouce(), color:0x9a6ae8, transparent:true, opacity:0.4,
    blending:THREE.AdditiveBlending, depthWrite:false }));
  halo.scale.setScalar(1.7); halo.position.y = 1.0;
  g.add(halo);

  const blob = new THREE.Mesh(geo.blob, matBlob);
  blob.rotation.x = -Math.PI/2; blob.position.set(0, 0.03, 0);
  g.add(blob);

  g.userData.corps = robe;             // la boucle du jeu anime son opacité
  g.userData._anim = { robe2, halo, ph: opts.ph || 0 };
  return g;
}

/* ─────────────────────────── LE REGISTRE ─────────────────────────── */
const REGISTRE = {
  'creature.rat': {
    componentId: 'creature.rat', version: 1, category: 'creature',
    type: 'rat', nom: 'Rat des caves',
    scale: 0.7, anchor: { y: 0 }, hauteurBarre: 1.35,
    qualite: 'L3', ombre: { cast: true, receive: false, blob: true },
    construit: construireRat,
    metadata: {
      dimensions: { l: 0.8, p: 0.5, h: 0.45 },
      animations: ['queue'],
      source: 'components/creatures.js',
    },
  },
  'creature.spectre': {
    componentId: 'creature.spectre', version: 1, category: 'creature',
    type: 'spectre', nom: 'Spectre',
    scale: 1.0, anchor: { y: 0 }, hauteurBarre: 2.3,
    qualite: 'L3', ombre: { cast: false, receive: false, blob: true },
    construit: construireSpectre,
    metadata: {
      dimensions: { l: 1.0, p: 1.0, h: 1.7 },
      animations: ['robe', 'halo'],
      source: 'components/creatures.js',
    },
  },
};

const _instances = [];

function construire(componentId, opts = {}){
  const def = REGISTRE[componentId];
  if(!def) return null;
  const g = def.construit({ ph: opts.ph || 0, qualite: opts.qualite || def.qualite });
  g.userData.componentId = componentId;
  g.userData.type = def.type;
  g.scale.setScalar(opts.scale || def.scale);
  _instances.push(g);
  return g;
}

function trouver(type){
  for(const id in REGISTRE) if(REGISTRE[id].type === type) return REGISTRE[id];
  return null;
}

function liste(){
  return Object.values(REGISTRE).map(d => ({
    componentId: d.componentId, version: d.version, category: d.category,
    type: d.type, nom: d.nom, scale: d.scale, qualite: d.qualite,
    metadata: d.metadata,
  }));
}

/* ─────────────── l'animation d'idle (dans le module, pas le jeu) ─────────────── */
let _t0 = 0;
function _boucle(t){
  const now = t / 1000;
  if(!_t0) _t0 = now;
  const dt = Math.min(0.05, now - _t0); _t0 = now;
  for(const g of _instances){
    const a = g.userData._anim;
    if(!a) continue;
    if(g.userData.type === 'rat' && a.queue){
      a.queue.rotation.z = Math.sin(now * 5 + a.ph) * 0.35;      // queue qui fouette
      a.queue.rotation.y = Math.sin(now * 2.4 + a.ph) * 0.5;
    } else if(g.userData.type === 'spectre'){
      a.robe2.rotation.y += dt * 0.4;                            // la robe intérieure tourne
      a.halo.material.opacity = 0.32 + Math.sin(now * 2 + a.ph) * 0.1;
    }
  }
  requestAnimationFrame(_boucle);
}
requestAnimationFrame(_boucle);

window.CREATURES = { REGISTRE, construire, trouver, liste };
