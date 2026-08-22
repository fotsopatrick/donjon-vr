/* world-builder-ui.js — l'interface de construction par intention (P0.5).

   Mode constructeur (touche B ou bouton en haut à droite) :
     · clic sur un objet world builder  → sélection (ID connu, état affiché)
     · clic sur le terrain              → position cible (marqueur) pour le
       prochain objet généré, OU déplacement de l'objet sélectionné si le
       mode « Déplacer » est armé
   Panneau minimal : référence (optionnelle), intention → Générer, et pour
   l'objet sélectionné une modification conversationnelle → Envoyer.
   Tout passe par le pont local (world_builder/bridge.py, 127.0.0.1:8765).
   Le pipeline Blender/registre/scène existant n'est JAMAIS contourné.

   Honnêteté vision : si le pont rapporte « palette seule », l'interface le
   dit à l'utilisateur — elle ne prétend pas analyser visuellement une image.
*/
import * as THREE from './three.module.js';

const K = window.KOTOAGE;
const WB = window.WB;
const PONT = window.WB_PONT_URL || 'http://127.0.0.1:8765';

const raycaster = new THREE.Raycaster();
const ndc = new THREE.Vector2();
const planSol = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
const DISTANCE_MAX = 60;

const ui = {
  actif: false,
  selection: null,      // { id }
  posCible: null,       // { x, z }
  deplacerArme: false,
  refImageB64: null,
  pointerDown: { x: 0, y: 0 },
  marqueurPos: null,    // Object3D
  marqueurSel: null,    // Object3D
};

/* ═══════════════ DOM ═══════════════ */
const styleUi = document.createElement('style');
styleUi.textContent = `
  #wbui-bouton{position:fixed;top:14px;right:14px;z-index:98;padding:9px 14px;
    border:1px solid rgba(215,190,130,.55);border-radius:8px;background:rgba(16,13,9,.82);
    color:#d8be86;font:inherit;font-size:12px;letter-spacing:.04em;cursor:pointer}
  #wbui-bouton:hover,#wbui-bouton.on{background:rgba(43,35,23,.95);box-shadow:0 0 12px rgba(215,190,130,.35)}
  #wbui-panneau{position:fixed;top:60px;right:14px;z-index:97;width:320px;max-height:calc(100vh - 80px);
    overflow:auto;background:rgba(10,9,7,.92);border:1px solid rgba(215,190,130,.35);border-radius:10px;
    color:#d8be86;font:13px/1.5 system-ui,sans-serif;box-shadow:0 6px 30px rgba(0,0,0,.6)}
  #wbui-panneau.cache{display:none}
  .wbui-tete{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;
    border-bottom:1px solid rgba(215,190,130,.25);font-weight:600;letter-spacing:.06em}
  .wbui-fermer{background:none;border:none;color:#d8be86;font-size:18px;cursor:pointer;padding:0 4px}
  .wbui-corps{padding:12px 14px}
  .wbui-section{margin-bottom:14px;padding-bottom:12px;border-bottom:1px dashed rgba(215,190,130,.18)}
  .wbui-section:last-child{border-bottom:none;margin-bottom:0;padding-bottom:0}
  .wbui-titre{font-size:11px;letter-spacing:.12em;color:#a08a5a;text-transform:uppercase;margin-bottom:6px}
  .wbui-obj{background:rgba(0,0,0,.35);border:1px solid rgba(215,190,130,.2);border-radius:6px;padding:8px 10px;margin-bottom:8px}
  .wbui-label{display:block;font-size:11px;color:#a08a5a;margin:6px 0 3px}
  #wbui-ref{width:100%;font:inherit;color:#d8be86;font-size:11px}
  #wbui-intention,#wbui-modif{width:100%;box-sizing:border-box;background:rgba(6,10,18,.9);color:#dceaff;
    border:1px solid rgba(90,168,255,.3);border-radius:6px;padding:8px 10px;font:inherit;resize:vertical}
  .wbui-note{font-size:11px;color:#9aa8a8;margin:4px 0 2px;line-height:1.4}
  .wbui-note-alerte{color:#ff9a6a}
  .wbui-position{font-size:12px;margin:8px 0 2px}
  .wbui-bouton{margin-top:8px;width:100%;padding:9px 12px;border:1px solid #5c4a2a;border-radius:6px;
    background:linear-gradient(180deg,#1d1811,#100d09);color:#d8be86;font:inherit;cursor:pointer}
  .wbui-bouton:hover{background:linear-gradient(180deg,#2b2317,#171208)}
  .wbui-bouton.wbui-principal{border-color:#3d7a6a;color:#bfe8dc;background:linear-gradient(180deg,#12322b,#0a1f1a)}
  .wbui-bouton.wbui-principal:hover{background:linear-gradient(180deg,#1a443a,#0e2a22)}
  .wbui-bouton:disabled{opacity:.5;cursor:wait}
  .wbui-statut{margin-top:10px;font-size:12px;line-height:1.45;color:#9fc4ee}
  .wbui-statut.wbui-ok{color:#9fe8c0}.wbui-statut.wbui-err{color:#ff8a7a}
  .wbui-statut.wbui-warn{color:#ffd77a}.wbui-statut.wbui-busy{color:#9fc4ee}
`;
document.head.appendChild(styleUi);

const H = document.createElement('div');
H.id = 'wbui-panneau';
H.className = 'cache';   // masqué tant que le mode constructeur n'est pas actif
H.innerHTML = `
  <div class="wbui-tete">
    <span>🧱 Constructeur</span>
    <button type="button" class="wbui-fermer" title="Fermer (B)">×</button>
  </div>
  <div class="wbui-corps">
    <div class="wbui-section" id="wbui-sel">
      <div class="wbui-titre">Objet sélectionné</div>
      <div class="wbui-obj" id="wbui-sel-infos"><i>aucun — clique sur un bâtiment</i></div>
      <button type="button" class="wbui-bouton" id="wbui-deplacer">Déplacer (clic sur le terrain)</button>
    </div>
    <div class="wbui-section">
      <div class="wbui-titre">Créer un bâtiment</div>
      <label class="wbui-label">Référence visuelle (optionnelle)</label>
      <input type="file" id="wbui-ref" accept="image/png,image/jpeg,image/webp">
      <div class="wbui-note" id="wbui-note-vision"></div>
      <label class="wbui-label">Intention</label>
      <textarea id="wbui-intention" rows="2" placeholder="Ex. : petite maison nordique en bois sombre, toit très pentu, légèrement vieillie, avec de la mousse."></textarea>
      <div class="wbui-position" id="wbui-pos">Position cible : <b>clique sur le terrain</b></div>
      <button type="button" class="wbui-bouton wbui-principal" id="wbui-generer">Générer et placer</button>
    </div>
    <div class="wbui-section" id="wbui-mod-section">
      <div class="wbui-titre">Modifier l'objet sélectionné</div>
      <textarea id="wbui-modif" rows="2" placeholder="Ex. : ajoute une cheminée et vieillis davantage le bois."></textarea>
      <button type="button" class="wbui-bouton wbui-principal" id="wbui-envoyer">Envoyer la modification</button>
    </div>
    <div class="wbui-statut" id="wbui-statut"></div>
  </div>
`;
const bouton = document.createElement('button');
bouton.id = 'wbui-bouton';
bouton.textContent = '🧱 Construire (B)';
bouton.title = 'Mode constructeur — clic terrain pour placer, clic objet pour sélectionner';
document.body.appendChild(bouton);
document.body.appendChild(H);

const ref = {
  fermer: H.querySelector('.wbui-fermer'),
  selInfos: H.querySelector('#wbui-sel-infos'),
  btnDeplacer: H.querySelector('#wbui-deplacer'),
  refInput: H.querySelector('#wbui-ref'),
  noteVision: H.querySelector('#wbui-note-vision'),
  intention: H.querySelector('#wbui-intention'),
  pos: H.querySelector('#wbui-pos'),
  generer: H.querySelector('#wbui-generer'),
  modif: H.querySelector('#wbui-modif'),
  envoyer: H.querySelector('#wbui-envoyer'),
  statut: H.querySelector('#wbui-statut'),
};

function setStatut(msg, type = 'ok') {
  ref.statut.textContent = msg;
  ref.statut.className = 'wbui-statut wbui-' + type;
}

/* ═══════════════ pont ═══════════════ */
async function api(route, corps) {
  const rep = await fetch(PONT + route, {
    method: corps ? 'POST' : 'GET',
    headers: corps ? { 'Content-Type': 'application/json' } : undefined,
    body: corps ? JSON.stringify(corps) : undefined,
  });
  let d = {};
  try { d = await rep.json(); } catch (e) { /* pas de JSON */ }
  if (!rep.ok) throw new Error(d.erreur || ('HTTP ' + rep.status));
  return d;
}

/* ═══════════════ mode constructeur ═══════════════ */
function basculerMode() {
  ui.actif = !ui.actif;
  H.classList.toggle('cache', !ui.actif);
  bouton.textContent = ui.actif ? '🧱 Quitter le constructeur (B)' : '🧱 Construire (B)';
  bouton.classList.toggle('on', ui.actif);
  rendererCursor();
  if (ui.actif) {
    document.exitPointerLock?.();
    if (!K.estDehors) setStatut('Le constructeur place au hameau (niveau 0) — tu es ailleurs.', 'warn');
  } else {
    desactiverDeplacer();
    clearPosCible();
    effacerSelection();
    setStatut('');
    try { renderer.domElement.requestPointerLock(); } catch (e) { /* pas grave */ }
  }
  window.WBUI = { enModeConstructeur: ui.actif };
}

function rendererCursor() {
  renderer.domElement.style.cursor = ui.actif ? 'crosshair' : '';
}

const renderer = K.renderer;

/* ═══════════════ raycast ═══════════════ */
function trouverId(obj) {
  let n = obj;
  while (n) {
    if (n.userData && n.userData.id) return n.userData.id;
    n = n.parent;
  }
  return null;
}

function clicSurCanvas(event) {
  if (!ui.actif) return;
  if (Math.hypot(event.clientX - ui.pointerDown.x, event.clientY - ui.pointerDown.y) > 6) return; // drag = rotation

  const r = renderer.domElement.getBoundingClientRect();
  ndc.x = ((event.clientX - r.left) / r.width) * 2 - 1;
  ndc.y = -((event.clientY - r.top) / r.height) * 2 + 1;
  raycaster.setFromCamera(ndc, K.camera);

  // 1) un objet world builder ?  → sélection / déplacement
  const racines = [...WB.objets.values()].map(v => v.obj3d);
  if (racines.length) {
    const touches = raycaster.intersectObjects(racines, true);
    for (const t of touches) {
      const id = trouverId(t.object);
      if (id) {
        if (ui.deplacerArme) desactiverDeplacer();
        select(id);
        return;
      }
    }
  }

  // 2) sinon : le terrain → position cible ou déplacement
  const cible = new THREE.Vector3();
  if (raycaster.ray.intersectPlane(planSol, cible)) {
    if (raycaster.ray.distanceToPoint(cible) > DISTANCE_MAX) return;
    if (ui.deplacerArme && ui.selection) {
      deplacerVers(cible.x, cible.z);
    } else {
      poserPosCible(cible.x, cible.z);
    }
  }
}

renderer.domElement.addEventListener('pointerdown', e => {
  ui.pointerDown = { x: e.clientX, y: e.clientY };
  if (!ui.actif || e.button !== 0) return;
});
renderer.domElement.addEventListener('click', clicSurCanvas);

/* ═══════════════ position cible ═══════════════ */
function poserPosCible(x, z) {
  ui.posCible = { x: Math.round(x * 100) / 100, z: Math.round(z * 100) / 100 };
  ref.pos.innerHTML = 'Position cible : <b>' + ui.posCible.x + ' , ' + ui.posCible.z + '</b> (clique ailleurs pour déplacer)';
  if (!ui.marqueurPos) {
    const anneau = new THREE.Mesh(
      new THREE.RingGeometry(0.45, 0.7, 32),
      new THREE.MeshBasicMaterial({ color: 0x7cf07c, transparent: true, opacity: 0.9, side: THREE.DoubleSide, depthWrite: false }));
    anneau.rotation.x = -Math.PI / 2;
    const pique = new THREE.Mesh(
      new THREE.ConeGeometry(0.12, 0.9, 12),
      new THREE.MeshBasicMaterial({ color: 0x7cf07c }));
    pique.position.y = 0.45;
    ui.marqueurPos = new THREE.Group();
    ui.marqueurPos.add(anneau, pique);
    K.scene.add(ui.marqueurPos);
  }
  ui.marqueurPos.position.set(x, 0, z);
  ui.marqueurPos.visible = K.niveau === 0;
}

function clearPosCible() {
  ui.posCible = null;
  ref.pos.innerHTML = 'Position cible : <b>clique sur le terrain</b>';
  if (ui.marqueurPos) ui.marqueurPos.visible = false;
}

/* ═══════════════ sélection ═══════════════ */
async function select(id) {
  ui.selection = { id };
  const e = WB.objets.get(id);
  if (e && e.etat.lieu !== K.niveau) {
    ref.selInfos.innerHTML = '<b>' + id + '</b><br><i>à un autre niveau (lieu ' + e.etat.lieu + ') — inaccessible ici</i>';
    return;
  }
  afficherMarqueurSelection(id);
  try {
    const o = await api('/api/objet?id=' + encodeURIComponent(id));
    const s = o.objet_en_scene;
    const p = s.position;
    ref.selInfos.innerHTML =
      '<b>' + o.id + '</b><br>' +
      'Asset : ' + o.versions.find(v => v.version === o.activeVersion).file.split('/').pop() + '<br>' +
      'Position : ' + p.x + ' , ' + p.z + '<br>' +
      'Rotation : ' + s.rotationY + ' · Échelle : ' + s.echelle + '<br>' +
      'Version : ' + o.activeVersion + '<br>' +
      'Matériaux : ' + (o.meta.materials || []).join(', ') || '—';
  } catch (e) {
    ref.selInfos.innerHTML = '<b>' + id + '</b><br><i>' + e.message + '</i>';
  }
}

function afficherMarqueurSelection(id) {
  const e = WB.objets.get(id);
  if (!e) return;
  if (!ui.marqueurSel) {
    const anneau = new THREE.Mesh(
      new THREE.RingGeometry(0.8, 1.05, 32),
      new THREE.MeshBasicMaterial({ color: 0xffd77a, transparent: true, opacity: 0.95, side: THREE.DoubleSide, depthWrite: false }));
    anneau.rotation.x = -Math.PI / 2;
    ui.marqueurSel = new THREE.Group();
    ui.marqueurSel.add(anneau);
    K.scene.add(ui.marqueurSel);
  }
  const p = e.etat.position;
  ui.marqueurSel.position.set(p.x, 0.05, p.z);
  ui.marqueurSel.visible = e.etat.lieu === K.niveau;
}

function effacerSelection() {
  ui.selection = null;
  ref.selInfos.innerHTML = '<i>aucun — clique sur un bâtiment</i>';
  if (ui.marqueurSel) ui.marqueurSel.visible = false;
}

/* ═══════════════ déplacement ═══════════════ */
async function deplacerVers(x, z) {
  const id = ui.selection.id;
  ui.deplacerArme = false;
  ref.btnDeplacer.textContent = 'Déplacer (clic sur le terrain)';
  try {
    const r = await api('/api/deplacer', { id, x: Math.round(x * 100) / 100, z: Math.round(z * 100) / 100 });
    WB.deplace(id, r.position.x, r.position.z);
    afficherMarqueurSelection(id);
    await select(id);
    setStatut('✓ ' + id + ' déplacé en ' + r.position.x + ' , ' + r.position.z, 'ok');
  } catch (e) {
    setStatut('✗ ' + e.message, 'err');
  }
}

function armerDeplacer() {
  if (!ui.selection) { setStatut('Sélectionne d\'abord un objet.', 'warn'); return; }
  ui.deplacerArme = true;
  ref.btnDeplacer.textContent = 'Clique sur le terrain pour y déplacer ' + ui.selection.id + '…';
  setStatut('Clique sur le terrain pour déplacer ' + ui.selection.id + '.', 'warn');
}

function desactiverDeplacer() {
  ui.deplacerArme = false;
  ref.btnDeplacer.textContent = 'Déplacer (clic sur le terrain)';
}

/* ═══════════════ génération ═══════════════ */
async function genererEtPlacer() {
  const demande = ref.intention.value.trim();
  if (!demande) { setStatut('Décris ce que tu veux construire.', 'warn'); return; }
  const corps = { demande, lieu: 0 };
  if (ui.posCible) corps.pos = ui.posCible;
  if (ui.refImageB64) corps.imageB64 = ui.refImageB64;
  setStatut('Génération en cours — Blender travaille (peut prendre 30 s à 2 min)…', 'busy');
  ref.generer.disabled = true;
  try {
    const r = await api('/api/creer', corps);
    await WB.recharger();
    await select(r.id);
    clearPosCible();
    const refNote = (r.ref_faits && r.ref_faits.avertissement) ? ' (' + r.ref_faits.avertissement + ')' : '';
    setStatut('✓ ' + r.id + ' placé en ' + r.position.x + ' , ' + r.position.z +
      ' — v1, ' + r.octets + ' o, ' + r.triangles + ' tris. Spec : ' + r.spec_source + refNote, 'ok');
  } catch (e) {
    setStatut('✗ ' + e.message, 'err');
  } finally {
    ref.generer.disabled = false;
  }
}

/* ═══════════════ modification conversationnelle ═══════════════ */
async function envoyerModification() {
  if (!ui.selection) { setStatut('Sélectionne d\'abord un objet.', 'warn'); return; }
  const demande = ref.modif.value.trim();
  if (!demande) { setStatut('Décris la modification.', 'warn'); return; }
  const id = ui.selection.id;
  setStatut('Modification de ' + id + ' en cours — Blender travaille…', 'busy');
  ref.envoyer.disabled = true;
  try {
    const r = await api('/api/modifier', { id, demande });
    await WB.recharger();
    await select(id);
    if (r.geometrique) {
      setStatut('✓ ' + id + ' modifié — nouvelle version v' + r.nouvelleVersion +
        ' (' + r.octets + ' o, ' + r.triangles + ' tris). Le même ID est conservé.', 'ok');
    } else {
      setStatut('✓ ' + id + ' transformé (position/échelle/rotation, pas de nouvelle version).', 'ok');
    }
  } catch (e) {
    setStatut('✗ ' + e.message, 'err');
  } finally {
    ref.envoyer.disabled = false;
  }
}

/* ═══════════════ référence + honnêteté vision ═══════════════ */
ref.refInput.addEventListener('change', async () => {
  const f = ref.refInput.files[0];
  if (!f) return;
  if (!/image\/(png|jpeg|jpg|webp)/.test(f.type)) {
    setStatut('Format non supporté : PNG, JPEG ou WebP.', 'warn');
    ui.refImageB64 = null;
    ref.noteVision.textContent = '';
    return;
  }
  const reader = new FileReader();
  reader.onload = () => { ui.refImageB64 = reader.result; };
  reader.readAsDataURL(f);
  ref.noteVision.textContent = 'Référence « ' + f.name + ' » retenue.';
  try {
    const v = await api('/api/vision');
    if (!v.vision_reelle) {
      ref.noteVision.textContent += ' — ATTENTION : analyse par palette de couleurs seule (pas de vision réelle). Architecture et proportions de l\'image ne seront pas mesurées.';
      ref.noteVision.className = 'wbui-note wbui-note-alerte';
    } else {
      ref.noteVision.textContent += ' — analyse visuelle : ' + (v.modele || 'modèle vision');
      ref.noteVision.className = 'wbui-note';
    }
  } catch (e) { /* le pont n'est pas là : l'image reste retenue pour la création */ }
});

/* ═══════════════ évènements ═══════════════ */
bouton.addEventListener('click', basculerMode);
ref.fermer.addEventListener('click', () => { if (ui.actif) basculerMode(); });
ref.generer.addEventListener('click', genererEtPlacer);
ref.envoyer.addEventListener('click', envoyerModification);
ref.btnDeplacer.addEventListener('click', armerDeplacer);

document.addEventListener('keydown', e => {
  if (e.code !== 'KeyB' || e.repeat) return;
  const t = e.target;
  if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
  e.preventDefault();
  basculerMode();
}, true);

/* ═══════════════ visibilité du niveau (le WB change d'étage tout seul) ═══════════════ */
setInterval(() => {
  if (ui.marqueurPos) ui.marqueurPos.visible = (ui.posCible !== null) && K.niveau === 0;
  if (ui.marqueurSel && ui.selection) {
    const e = WB.objets.get(ui.selection.id);
    if (e) ui.marqueurSel.visible = e.etat.lieu === K.niveau;
  }
}, 500);

setTimeout(async () => {
  try {
    const e = await api('/api/etat');
    const n = e.scene.objets.length;
    bouton.title += ' — pont ' + PONT + ' (répond, ' + n + ' objet(s))';
    setStatut('Pont local connecté (' + PONT + ') — ' + n + ' objet(s) au hameau.', 'ok');
  } catch (err) {
    setStatut('Pont ' + PONT + ' injoignable — lance : python3 -m world_builder.bridge', 'err');
  }
}, 800);

export { basculerMode };
