/* world-builder.js — le runtime Three.js du AI World Builder (P0).

Charge monde/scene.json (écrit par l'orchestrateur Python), place chaque
objet dans la scène du jeu avec son ID logique persistant, et expose window.WB
pour retrouver / déplacer / redimensionner / remplacer un objet sans toucher
à Blender. Les GLB sont chargés par le GLTFLoader du jeu (pas de second loader).

Convention (consigne P0 point 7) : l'ID logique (building_001) reste stable ;
seule la VERSION du GLB change (maison_001_v1.glb -> v2). L'objet 3D porte
l'ID dans userData.id.
*/
import * as THREE from './three.module.js';
import { GLTFLoader } from './jsm/loaders/GLTFLoader.js';

const K = window.KOTOAGE;
const SCENE_URL = 'monde/scene.json';
const NB_MAX = 64;

const groupe = new THREE.Group();
groupe.name = 'world-builder';
K.scene.add(groupe);

const loader = new GLTFLoader();
const objets = new Map();          // id -> { obj3d, etat }

let dernierNiveau = null;

function chargerGlb(fichier) {
  return new Promise((res, rej) => {
    loader.load(fichier, g => {
      const racine = g.scene;
      racine.traverse(o => {
        if (o.isMesh) {
          o.frustumCulled = false;
          o.castShadow = true;
          o.receiveShadow = true;
          if (o.material && o.material.color) o.material.color.multiplyScalar(1);
        }
      });
      res(racine);
    }, undefined, () => rej(new Error('GLB introuvable : ' + fichier)));
  });
}

function appliquerTransfo(obj3d, etat) {
  const p = etat.position || { x: 0, z: 0 };
  obj3d.position.set(p.x, etat.position && etat.position.y ? etat.position.y : 0, p.z);
  obj3d.rotation.y = etat.rotationY || 0;
  obj3d.scale.setScalar(etat.echelle || 1);
}

async function poserObjet(etat) {
  const racine = await chargerGlb(etat.assetFile);
  racine.userData.id = etat.id;
  appliquerTransfo(racine, etat);
  groupe.add(racine);
  objets.set(etat.id, { obj3d: racine, etat });
  majVisibilite();
  return racine;
}

function majVisibilite() {
  const n = K.niveau;
  for (const { obj3d, etat } of objets.values()) {
    obj3d.visible = (etat.lieu === n);
  }
  dernierNiveau = n;
}

async function chargerScene() {
  try {
    const rep = await fetch(SCENE_URL);
    if (!rep.ok) return { chargés: 0, total: 0 };
    const sc = await rep.json();
    const liste = (sc.objets || []).slice(0, NB_MAX);
    let ok = 0;
    for (const o of liste) {
      try {
        await poserObjet(o);
        ok++;
      } catch (e) {
        console.warn('[WB] objet non posé', o.id, e.message);
      }
    }
    return { chargés: ok, total: liste.length };
  } catch (e) {
    return { chargés: 0, total: 0, erreur: e.message };
  }
}

setInterval(() => {
  if (K.niveau !== dernierNiveau) majVisibilite();
}, 500);

const WB = {
  objets,

  async recharger() {
    while (groupe.children.length) groupe.remove(groupe.children[0]);
    objets.clear();
    return chargerScene();
  },

  liste() {
    return [...objets.values()].map(({ etat }) => ({
      id: etat.id,
      version: etat.assetVersion,
      assetFile: etat.assetFile,
      lieu: etat.lieu,
      position: etat.position,
      rotationY: etat.rotationY,
      echelle: etat.echelle,
    }));
  },

  trouver(id) {
    const e = objets.get(id);
    return e ? { obj3d: e.obj3d, etat: e.etat } : null;
  },

  etat(id) {
    const e = objets.get(id);
    return e ? { ...e.etat, position: { ...e.etat.position } } : null;
  },

  deplace(id, x, z) {
    const e = objets.get(id);
    if (!e) return { ok: false, raison: 'id inconnu' };
    e.etat.position.x = x;
    e.etat.position.z = z;
    e.obj3d.position.set(x, 0, z);
    return { ok: true, position: e.etat.position };
  },

  echelle(id, s) {
    const e = objets.get(id);
    if (!e) return { ok: false, raison: 'id inconnu' };
    e.etat.echelle = s;
    e.obj3d.scale.setScalar(s);
    return { ok: true, echelle: s };
  },

  rotation(id, degres) {
    const e = objets.get(id);
    if (!e) return { ok: false, raison: 'id inconnu' };
    e.etat.rotationY = degres * Math.PI / 180;
    e.obj3d.rotation.y = e.etat.rotationY;
    return { ok: true, rotationY: e.etat.rotationY };
  },

  async remplacer(id) {
    const e = objets.get(id);
    if (!e) return { ok: false, raison: 'id inconnu' };
    const nouvelle = await chargerGlb(e.etat.assetFile);
    nouvelle.userData.id = id;
    appliquerTransfo(nouvelle, e.etat);
    groupe.remove(e.obj3d);
    groupe.add(nouvelle);
    e.obj3d = nouvelle;
    majVisibilite();
    return { ok: true, id, assetFile: e.etat.assetFile, version: e.etat.assetVersion };
  },

  retirer(id) {
    const e = objets.get(id);
    if (!e) return { ok: false, raison: 'id inconnu' };
    groupe.remove(e.obj3d);
    objets.delete(id);
    return { ok: true };
  },

  sauver() {
    return { version: 1, objets: this.liste() };
  },

  telecharger() {
    const texte = JSON.stringify(this.sauver(), null, 2);
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([texte], { type: 'application/json' }));
    a.download = 'scene.json';
    a.click();
    return { ok: true, texte };
  },
};

window.WB = WB;

chargerScene();
