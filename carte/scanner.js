// scanner.js — LA CARTE VIVANTE DU JEU : il ouvre le jeu, visite chaque lieu,
// et note CE QUI EXISTE VRAIMENT. Pas ce qu'on croit : ce que la scène contient.
//
// Pourquoi (Patrick, 21/08) : « tu n'arrives pas à avoir un inventaire du jeu ?
// il te faut peut-être une carte vivante du jeu ». Chaque défaut de la journée
// venait du même trou : je corrigeais un endroit et j'en ratais quatre.
//
// Usage : node carte/scanner.js [port]   → écrit carte/inventaire.json
const http = require('http'), fs = require('fs'), path = require('path');
const PORT = process.argv[2] || 9280;
const SORTIE = path.join(__dirname, 'inventaire.json');

const getJSON = p => new Promise((r, j) =>
  http.get('http://127.0.0.1:' + PORT + p, x => { let d = ''; x.on('data', c => d += c); x.on('end', () => { try { r(JSON.parse(d)); } catch (e) { j(e); } }); }).on('error', j));
const dodo = ms => new Promise(r => setTimeout(r, ms));

// Les lieux à visiter. « depart » = comment on y entre.
const LIEUX = [
  { id: 'village',  nom: 'Le hameau et la route',  hash: '#village', niveau: 0 },
  { id: 'arene',    nom: "L'arène d'entraînement", hash: '#arene',   niveau: -1 },
  { id: 'donjon1',  nom: 'Donjon — les caves',     hash: '#donjon',  niveau: 1 },
  { id: 'donjon2',  nom: "Donjon — l'ossuaire",    hash: '#donjon',  niveau: 2 },
  { id: 'donjon3',  nom: 'Donjon — la clairière',  hash: '#donjon',  niveau: 3 },
  { id: 'donjon4',  nom: 'Donjon — le voile',      hash: '#donjon',  niveau: 4 },
  { id: 'donjon5',  nom: 'Donjon — le palier',     hash: '#donjon',  niveau: 5 },
];

(async () => {
  const onglets = await getJSON('/json');
  const page = onglets.find(x => x.type === 'page' && x.webSocketDebuggerUrl);
  if (!page) { console.log('AUCUNE PAGE : le navigateur de scan est-il lancé ?'); process.exit(2); }
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0; const attentes = {};
  const envoyer = (m, p) => new Promise(r => { const i = ++id; attentes[i] = r; ws.send(JSON.stringify({ id: i, method: m, params: p || {} })); });
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && attentes[m.id]) { attentes[m.id](m.result || {}); delete attentes[m.id]; } };
  await new Promise(r => ws.onopen = r);
  await envoyer('Runtime.enable'); await envoyer('Page.enable');
  const lire = async x => { const { result } = await envoyer('Runtime.evaluate', { expression: x, returnByValue: true }); return result && result.value; };

  const inventaire = { releve_le: new Date().toISOString(), lieux: [] };

  for (const lieu of LIEUX) {
    process.stdout.write('  ' + lieu.nom + ' … ');
    await envoyer('Page.navigate', { url: 'about:blank' }); await dodo(200);
    await envoyer('Page.navigate', { url: 'http://127.0.0.1:8099/index.html?t=' + Date.now() + lieu.hash });
    // on attend que le jeu démarre pour de bon
    let parti = false;
    for (let i = 0; i < 40 && !parti; i++) {
      await lire('(function(){var b=document.getElementById("jouer");if(b&&!b.disabled&&window.D&&window.D.etat!=="jeu")b.click();})()');
      await dodo(1200);
      parti = (await lire('window.D&&window.D.etat')) === 'jeu';
    }
    if (!parti) { console.log('PAS DÉMARRÉ'); inventaire.lieux.push({ ...lieu, erreur: 'le jeu ne démarre pas' }); continue; }
    if (lieu.niveau > 1) { await lire('window.D.allerA && window.D.allerA(' + lieu.niveau + ')'); await dodo(3500); }
    await dodo(2500);   // le temps que les fichiers lourds arrivent

    const brut = await lire(`(function(){
      var S = window.D.scene, T = window.D.T, out = {
        personnages: [], decors: {}, cercles: [], lumieres: [], grille: {}, sons: {}
      };
      // la grille : la taille du lieu
      var g = window.D.grid || [];
      out.grille = { largeur: window.D.W, hauteur: g.length, metres: [Math.round(window.D.W*T), Math.round(g.length*T)] };
      // les personnages
      out.personnages.push({ type:'joueur', nom:'toi', anime: !!(window.D.avatar && window.D.avatar.userData && window.D.avatar.userData.vrm) });
      if (window.D.guerrier) out.personnages.push({ type:'adversaire', nom:'guerrier', anime: !!window.D.guerrier.vrm });
      var vs = window.D.villageois || [];
      if (vs.length) out.personnages.push({ type:'villageois', nom:'habitants', nombre: vs.length,
        anime: !!(vs[0] && vs[0].os && vs[0].os.lUA), trajets: vs.filter(function(v){return (v.etapes||[]).length>1;}).length });
      var en = window.D.ennemis || [];
      if (en.length){ var parType = {}; en.forEach(function(e){ parType[e.type] = (parType[e.type]||0)+1; });
        Object.keys(parType).forEach(function(t){ out.personnages.push({ type:'monstre', nom:t, nombre:parType[t] }); }); }
      // les décors et les cercles, en parcourant la scène
      var compte = {};
      S.traverse(function(o){
        if (o.isMesh) {
          var geo = o.geometry && o.geometry.type || '?';
          compte[geo] = (compte[geo]||0)+1;
          var m = o.material;
          if (m && m.map && m.map.image && m.map.image.width === 512 && o.geometry.type !== 'SphereGeometry') {
            var p = new window.D.THREE.Vector3(); o.getWorldPosition(p);
            out.cercles.push({ forme:o.geometry.type, x:Math.round(p.x), z:Math.round(p.z), taille: o.geometry.parameters ? (o.geometry.parameters.width || o.geometry.parameters.radius || 0) : 0 });
          }
        }
        if (o.isLight) out.lumieres.push({ genre:o.type, couleur:'#'+o.color.getHexString(), force:Math.round(o.intensity*100)/100 });
      });
      out.decors = compte;
      // les sons
      out.sons = { voix_active: !!window.VOIX_ACTIVE, musique: (document.querySelectorAll('audio').length) };
      return JSON.stringify(out);
    })()`);

    let donnees = {};
    try { donnees = JSON.parse(brut); } catch (e) { donnees = { erreur: 'lecture impossible' }; }
    inventaire.lieux.push({ id: lieu.id, nom: lieu.nom, ...donnees });
    console.log('ok');
  }

  fs.writeFileSync(SORTIE, JSON.stringify(inventaire, null, 2));
  console.log('CARTE ÉCRITE :', SORTIE);
  ws.close(); process.exit(0);
})();
