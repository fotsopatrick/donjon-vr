/* inspection.js — MODE INSPECTION / CAPTURE reproductible (Phase A).
   Un registre de destinations PRÉDÉFINIES : téléportation + orientation caméra
   exactes, résolution/FOV fixes. Accessible :
     - dans le jeu : touche I → panneau de téléportation ;
     - par script : window.INSPECTION.points + window.INSPECTION.aller(p) ;
     - captures auto : tests/capturer-inspection.js (CDP), sortie dans
       tests/captures/inspection/.
   Ne modifie AUCUN gameplay : c'est une couche d'outil, jamais obligatoire. */
const T = window.D && window.D.T ? window.D.T : 2.6;

/* ─────────────────── LE REGISTRE DES DESTINATIONS ─────────────────── */
const POINTS = [
  // ── VILLAGE ──
  { cat:'Village', ciel:'village_golden', id:'01-spawn',            nom:'Spawn du village',      niveau:0, x:13*T, z:10*T,  lacet:0,   note:'Arrivée : la place et le hameau' },
  { cat:'Village', id:'02-place',            nom:'Place centrale',        niveau:0, x:13*T, z:9.7*T,  lacet:0,   note:'Le puits et la place pavée' },
  { cat:'Village', id:'03-rue',              nom:'Rue principale',        niveau:0, x:13*T, z:13*T,   lacet:3.14,note:'La rue vers la sortie' },
  { cat:'Village', id:'04-sortie',           nom:'Sortie du village',     niveau:0, x:13*T, z:17.6*T, lacet:3.14,note:'Le portail en travers de la rue' },
  { cat:'Village', id:'05-route-donjon',     nom:'Route vers le donjon',  niveau:0, x:13*T, z:22.2*T, lacet:-1.25,note:'Le coude vers le sentier' },
  { cat:'Village', id:'06-approche-donjon',  nom:'Sentier / approche',    niveau:0, x:11.6*T, z:23.0*T, lacet:3.14,note:'Le sentier de terre bordé' },
  { cat:'Village', id:'07-entree-donjon',    nom:'Entrée du donjon',      niveau:0, x:11.5*T, z:24.2*T, lacet:3.14,note:'L’arche de pierre et l’escalier' },
  { cat:'Village', id:'08-second-village',   nom:'Second village',        niveau:0, x:13*T, z:45*T,   lacet:3.14,note:'Sa place, son puits, sa croix' },
  { cat:'Village', id:'09-fermes',           nom:'Zone des fermes',       niveau:0, x:6.5*T, z:4.5*T, lacet:0,   note:'La ferme ouest, ses champs clôturés' },
  { cat:'Village', id:'10-bordure',          nom:'Bordure / transition',  niveau:0, x:2.5*T, z:20*T,  lacet:0,   note:'La lisière vers la forêt' },
  { cat:'Village', id:'11-aerienne',         nom:'Vue aérienne du village', niveau:0, x:13*T, z:9*T, lacet:3.14, tangage:-0.7, vol:true, hauteur:38, note:'Tout le hameau vu de haut' },
  { cat:'Village', ciel:'village_golden', id:'12-aerienne-donjon',  nom:'Vue aérienne vers le donjon', niveau:0, x:13*T, z:24*T, lacet:3.14, tangage:-0.55, vol:true, hauteur:38, note:'Le chemin vu depuis les airs' },

  // ── DONJON (étage 1 = PLAN_ETAGE1, reproductible) ──
  { cat:'Donjon', ciel:'village_golden', id:'d01-entree',           nom:'Entrée du donjon (é.1)', niveau:1, x:14.5*T, z:16.5*T, lacet:0,    note:'Spawn é.1, le cercle de téléportation à côté' },
  { cat:'Donjon', id:'d02-premiere-salle',   nom:'Première salle (é.1)',  niveau:1, x:8.5*T, z:8.5*T,  lacet:0,    note:'La salle ouest, le donjon central' },
  { cat:'Donjon', id:'d03-couloir',          nom:'Couloir (é.1)',         niveau:1, x:7.5*T, z:12.5*T, lacet:1.57, note:'Le passage est-ouest' },
  { cat:'Donjon', id:'d04-salle-decor',      nom:'Salle décorée (é.1)',   niveau:1, x:22.5*T, z:13.5*T, lacet:0,    note:'Salle à thème (trésor/crypte)' },
  { cat:'Donjon', id:'d05-salle-ennemis',    nom:'Salle avec ennemis (é.1)', niveau:1, x:4.5*T, z:4.5*T, lacet:3.14, note:'Le garde E à l’ouest' },
  { cat:'Donjon', id:'d06-salle-profonde',   nom:'Salle profonde (é.1)',  niveau:1, x:13.3*T, z:9.7*T, lacet:0,    note:'La salle du boss B au cœur' },
  { cat:'Donjon', id:'d07-transitions',      nom:'Transitions entre salles', niveau:1, x:14.5*T, z:13.5*T, lacet:0, note:'Le passage vers le donjon central' },

  // ── CRÉATURES (dans le VILLAGE, référence PBR lumineuse) ──
  { cat:'Créatures', id:'c-rat-seul',        nom:'Rat — seul',        creature:'rat',       niveau:0, px:13*T, pz:7.5*T, cx:13*T, cz:6.7*T, fige:true, tangage:-0.12,  note:'Volume, ancrage, matériau' },
  { cat:'Créatures', id:'c-rat-combat',      nom:'Rat — en combat',   creature:'rat',       niveau:0, px:13*T, pz:7.2*T, cx:13*T, cz:6.9*T, fige:false, tangage:-0.12, note:'Il s’approche' },
  { cat:'Créatures', id:'c-spectre-seul',    nom:'Spectre — seul',    creature:'spectre',   niveau:0, px:13*T, pz:7.5*T, cx:13*T, cz:6.7*T, fige:true, tangage:-0.12,  note:'Volume 3D flottant' },
  { cat:'Créatures', id:'c-spectre-combat',  nom:'Spectre — en combat',creature:'spectre',  niveau:0, px:13*T, pz:7.2*T, cx:13*T, cz:6.9*T, fige:false, tangage:-0.12, note:'Il s’approche' },
  { cat:'Créatures', id:'c-slime-seul',      nom:'Slime — seul',      creature:'slime',     niveau:0, px:13*T, pz:7.5*T, cx:13*T, cz:6.7*T, fige:true, tangage:-0.12,  note:'' },
  { cat:'Créatures', id:'c-slime-combat',    nom:'Slime — en combat', creature:'slime',     niveau:0, px:13*T, pz:7.2*T, cx:13*T, cz:6.9*T, fige:false, tangage:-0.12, note:'' },
  { cat:'Créatures', id:'c-squelette-seul',  nom:'Squelette — seul',  creature:'squelette', niveau:0, px:13*T, pz:7.5*T, cx:13*T, cz:6.7*T, fige:true, tangage:-0.12,  note:'' },
  { cat:'Créatures', id:'c-squelette-combat',nom:'Squelette — en combat',creature:'squelette',niveau:0, px:13*T, pz:7.2*T, cx:13*T, cz:6.9*T, fige:false, tangage:-0.12, note:'' },

  // ── CIEL / ATMOSPHÈRE ──
  { cat:'Ciel', id:'s-village-day',     nom:'Village — jour',      ciel:'village_day',     niveau:0, x:13*T, z:9.7*T, lacet:0 },
  { cat:'Ciel', id:'s-village-golden',  nom:'Village — heure dorée', ciel:'village_golden', niveau:0, x:13*T, z:9.7*T, lacet:0 },
  { cat:'Ciel', id:'s-night',           nom:'Village — nuit',      ciel:'night_fantasy',   niveau:0, x:13*T, z:9.7*T, lacet:0 },
  { cat:'Ciel', id:'s-magical',         nom:'Village — ciel magique', ciel:'magical_sky',   niveau:0, x:13*T, z:9.7*T, lacet:0 },
  { cat:'Ciel', id:'s-overcast',        nom:'Village — couvert',   ciel:'forest_overcast', niveau:0, x:13*T, z:9.7*T, lacet:0 },

  // ── UI ──
  { cat:'UI', id:'u-titre',  nom:'Menu principal', ui:'titre', note:'Écran titre, avant de jouer' },
  { cat:'UI', id:'u-hud',    nom:'HUD en jeu',     ui:'hud',   note:'Jauges, plaques, minimap' },
  { cat:'UI', id:'u-pause',  nom:'Menu pause',     ui:'pause', note:'Panneaux et onglets' },
];
// TOUTE destination de monde se fait sous le ciel doré par défaut : un point
// « nuit » précédent ne doit pas laisser le village sombre sur les suivants.
for(const _p of POINTS){
  if(!_p.ciel && (_p.cat === 'Village' || _p.cat === 'Donjon' || _p.cat === 'Créatures')){
    _p.ciel = 'village_golden';
  }
}

/* ─────────────────── TÉLÉPORTATION / ORIENTATION ─────────────────── */
function aller(pt){
  const D = window.D;
  if(!D) return 'pas de window.D';
  // UI : laissé au runner (DOM), mais on prépare l'état
  if(pt.ui){
    if(pt.ui === 'hud' && D.reprendreJeu) D.reprendreJeu();
    if(pt.ui === 'pause' && D.ouvrirPause) D.ouvrirPause();
    return;
  }
  if(pt.ciel && window.SKY) window.SKY.appliquer(pt.ciel);
  // créatures : on va dans l'arène et on en fabrique UNE, seule
  if(pt.creature){
    // on vient au village (lumineux, référence PBR) et on y place UNE créature.
    if(D.allerA && (!window.KOTOAGE || window.KOTOAGE.niveau !== 0)) D.allerA(0);
    D.joueur.vol = false; D.joueur.saut = 0;
    D.joueur.x = pt.px; D.joueur.z = pt.pz;
    D.joueur.lacet = 0; D.joueur.tangage = pt.tangage || -0.12;
    if(D.inspecterCreature){
      const e = D.inspecterCreature(pt.creature, pt.cx, pt.cz);
      if(e && pt.fige) e.cd = 9999;      // « seul » : il reste en place, face au joueur
    }
    return;
  }
  // destination normale
  if(pt.niveau !== undefined && window.KOTOAGE && window.KOTOAGE.niveau !== pt.niveau && D.allerA){
    D.allerA(pt.niveau);
  }
  D.joueur.vol = !!pt.vol;
  D.joueur.saut = pt.vol ? (pt.hauteur || 0) : 0;
  D.joueur.x = pt.x; D.joueur.z = pt.z;
  D.joueur.lacet = pt.lacet || 0;
  D.joueur.tangage = pt.tangage || 0;
}

/* ─────────────────── LE PANNEAU DANS LE JEU (touche I) ─────────────────── */
let _panneau = null, _ouvert = false;
function construirePanneau(){
  const style = document.createElement('style');
  style.textContent = `
    #inspect-panneau{position:fixed;right:16px;top:16px;z-index:60;width:min(340px,86vw);
      background:linear-gradient(180deg,rgba(22,17,12,.94),rgba(10,8,6,.96));
      border:1px solid rgba(196,148,80,.4);border-radius:4px;
      box-shadow:0 0 0 1px rgba(0,0,0,.6), 0 22px 60px rgba(0,0,0,.6);
      padding:12px 14px;color:#e8dcc0;font-family:"Iowan Old Style",Georgia,serif;
      max-height:84vh;overflow:auto;display:none}
    #inspect-panneau h3{margin:0 0 8px;font-size:13px;letter-spacing:.2em;color:var(--or,#e8b661);text-transform:uppercase}
    #inspect-panneau .cat{margin:8px 0 2px;font-size:11px;letter-spacing:.16em;color:#8f9ec0;text-transform:uppercase}
    #inspect-panneau button{display:block;width:100%;text-align:left;margin:3px 0;padding:6px 10px;
      border:1px solid rgba(120,95,55,.35);border-radius:3px;background:#171309;color:#d8be86;
      font:inherit;font-size:13px;cursor:pointer;transition:.2s}
    #inspect-panneau button:hover{border-color:#c8a04a;color:#ffe4ae;box-shadow:0 0 18px rgba(232,182,97,.2)}
    #inspect-close{margin-top:8px;text-align:center;color:#8a7c62;font-size:12px;cursor:pointer}`;
  document.head.appendChild(style);
  const p = document.createElement('div');
  p.id = 'inspect-panneau';
  p.innerHTML = '<h3>Inspection — téléportation</h3><div id="inspect-liste"></div>' +
                '<div id="inspect-close">fermer (I)</div>';
  document.body.appendChild(p);
  const liste = p.querySelector('#inspect-liste');
  let catCourante = '';
  for(const pt of POINTS){
    if(pt.cat !== catCourante){
      catCourante = pt.cat;
      const t = document.createElement('div');
      t.className = 'cat'; t.textContent = pt.cat;
      liste.appendChild(t);
    }
    const b = document.createElement('button');
    b.textContent = pt.id + ' — ' + pt.nom;
    b.title = pt.note || '';
    b.addEventListener('click', ()=>{ aller(pt); _ouvert = false; p.style.display = 'none'; });
    liste.appendChild(b);
  }
  p.querySelector('#inspect-close').addEventListener('click', ()=>{ _ouvert = false; p.style.display='none'; });
  return p;
}
function basculerPanneau(){
  if(!_panneau) _panneau = construirePanneau();
  _ouvert = !_ouvert;
  _panneau.style.display = _ouvert ? 'block' : 'none';
}
addEventListener('keydown', ev=>{
  if(ev.code === 'KeyI' && !ev.ctrlKey && !ev.metaKey){ ev.preventDefault(); basculerPanneau(); }
}, true);

window.INSPECTION = { points: POINTS, aller, basculerPanneau };
