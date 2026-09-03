// =====================================================================
//  tests/test_braignak_cdp.mjs — VRAIS tests, sur la vraie page.
// ---------------------------------------------------------------------
//  Ce banc lance SON PROPRE Chrome (profil jetable), charge la page du
//  jeu, et vérifie l'ÉTAT RÉEL du jeu à travers le pont
//  window.__webmcpConnexion. Il n'invente rien : chaque assertion lit
//  une vraie variable du module (les salles, leur thème, l'étude en
//  cours de Braignak).
//
//  Il ne teste PAS le rendu (une image), qui demande un écran : il teste
//  ce qui décide de ce rendu.
//
//  Usage :
//    node tests/test_braignak_cdp.mjs [url]
//    (défaut : la page live du bucket)
//
//  Sortie : « N/N verts » et code 0, ou la liste des échecs et code 1.
// =====================================================================
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const URL_DEFAUT = 'https://storage.googleapis.com/kotoage-webmcp-20260901-133904/index.html';
const url = process.argv[2] || URL_DEFAUT;
const PORT = 9500 + Math.floor(Math.random() * 300);
const profil = mkdtempSync(join(tmpdir(), 'kotoage-test-'));

const pause = (ms) => new Promise((r) => setTimeout(r, ms));

const chrome = spawn('google-chrome', [
  '--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${profil}`,
  '--window-size=1280,720', '--enable-unsafe-swiftshader', '--no-first-run',
  '--no-default-browser-check', '--mute-audio', '--disable-background-timer-throttling',
  'about:blank',
], { stdio: 'ignore', detached: true });

const nettoyer = () => {
  try { process.kill(-chrome.pid); } catch (e) {}
  try { rmSync(profil, { recursive: true, force: true }); } catch (e) {}
};

const resultats = [];
const verifier = (nom, condition, detail = '') => {
  resultats.push({ nom, ok: !!condition, detail });
  console.log((condition ? '  VERT  ' : '  ROUGE ') + nom + (condition ? '' : '  → ' + detail));
};

try {
  // --- connexion au navigateur -------------------------------------
  let tab = null;
  for (let i = 0; i < 40; i++) {
    try { tab = await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: 'PUT' })).json(); break; }
    catch (e) { await pause(500); }
  }
  if (!tab) throw new Error('Chrome ne répond pas sur le port ' + PORT);

  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((r) => (ws.onopen = r));
  let id = 1; const attente = new Map();
  ws.addEventListener('message', (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && attente.has(m.id)) {
      const { res, rej } = attente.get(m.id); attente.delete(m.id);
      m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result);
    }
  });
  const envoyer = (methode, params = {}) => new Promise((res, rej) => {
    const i = id++; attente.set(i, { res, rej });
    ws.send(JSON.stringify({ id: i, method: methode, params }));
  });
  const js = async (expr) =>
    (await envoyer('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true })).result.value;

  await envoyer('Network.enable');
  await envoyer('Network.setCacheDisabled', { cacheDisabled: true });
  await envoyer('Page.enable');
  await envoyer('Runtime.enable');
  await envoyer('Page.navigate', { url: url + (url.includes('?') ? '&' : '?') + 'v=' + Date.now() });

  // --- le jeu se charge --------------------------------------------
  let pret = false;
  for (let i = 0; i < 60; i++) { if (await js('!!window.__webmcpConnexion')) { pret = true; break; } await pause(1000); }
  verifier('le pont du jeu répond', pret, 'window.__webmcpConnexion absent après 60 s');
  if (!pret) throw new Error('jeu non chargé');

  // --- 1. les huit outils ------------------------------------------
  const nbOutils = await js('window.KOTOAGE_WEBMCP ? Object.keys(window.KOTOAGE_WEBMCP).length : 0');
  verifier('la couche WebMCP est chargée', nbOutils > 0, 'window.KOTOAGE_WEBMCP absent');

  // --- 2. le pont expose bien les nouvelles fonctions ----------------
  const pont = JSON.parse(await js(
    '(()=>{const c=window.__webmcpConnexion; return JSON.stringify({'
    + 'changerMap: typeof c.changerMap, braignakEtudier: typeof c.braignakEtudier, map: c.MAP_FORCEE});})()'));
  verifier('changerMap existe sur le pont', pont.changerMap === 'function', 'type reçu : ' + pont.changerMap);
  verifier('braignakEtudier existe sur le pont', pont.braignakEtudier === 'function', 'type reçu : ' + pont.braignakEtudier);
  verifier('au départ, aucune map forcée', pont.map === null, 'map = ' + pont.map);

  // --- 3. changerMap('serveur') : TOUTES les salles deviennent la salle serveurs
  const apresServeur = JSON.parse(await js(
    "(()=>{const c=window.__webmcpConnexion; const r=c.changerMap('serveur');"
    + ' const t=(c.rooms||[]).map(x=>x.theme);'
    + " return JSON.stringify({map:c.MAP_FORCEE, niveau:c.niveau, retour:r, salles:t.length, quantiques:t.filter(x=>x==='quantique').length, themes:[...new Set(t)]});})()"));
  verifier("changerMap('serveur') pose le drapeau", apresServeur.map === 'serveur', 'map = ' + apresServeur.map);
  verifier('la map serveur a des salles', apresServeur.salles > 0, apresServeur.salles + ' salle(s)');
  verifier('TOUTES les salles sont la salle serveurs',
    apresServeur.salles > 0 && apresServeur.quantiques === apresServeur.salles,
    apresServeur.quantiques + '/' + apresServeur.salles + ' — thèmes : ' + JSON.stringify(apresServeur.themes)
      + ' — niveau : ' + apresServeur.niveau + ' — retour : ' + JSON.stringify(apresServeur.retour));

  // --- 4. changerMap(null) : on revient à un donjon varié ------------
  const apresNormal = JSON.parse(await js(
    '(()=>{const c=window.__webmcpConnexion; c.changerMap(null);'
    + ' const t=(c.rooms||[]).map(r=>r.theme);'
    + " return JSON.stringify({map:c.MAP_FORCEE, salles:t.length, quantiques:t.filter(x=>x==='quantique').length, themes:[...new Set(t)]});})()"));
  verifier('changerMap(null) enlève le drapeau', apresNormal.map === null, 'map = ' + apresNormal.map);
  verifier('le donjon normal n\'est PAS tout en salle serveurs',
    apresNormal.salles > 0 && apresNormal.quantiques < apresNormal.salles,
    apresNormal.quantiques + '/' + apresNormal.salles + ' quantiques');

  // --- 5. Braignak prend une nouvelle étude --------------------------
  const etudeLancee = JSON.parse(await js(
    "(()=>{const c=window.__webmcpConnexion; c.braignakEtudier({sujet:'la couleur des torches', nouvelle:true});"
    + ' const e=c.braignakEtude; return JSON.stringify({en:!!e, sujet:e&&e.sujet, phase:e&&e.phase});})()'));
  verifier('une nouvelle étude démarre', etudeLancee.en === true, JSON.stringify(etudeLancee));
  verifier("l'étude retient le sujet demandé", etudeLancee.sujet === 'la couleur des torches', 'sujet = ' + etudeLancee.sujet);
  verifier("Braignak commence par chercher", etudeLancee.phase === 'cherche', 'phase = ' + etudeLancee.phase);

  // --- 6. une étude DÉJÀ menée ne déclenche aucune marche ------------
  const etudeConnue = JSON.parse(await js(
    "(()=>{const c=window.__webmcpConnexion; c.braignakEtudier(null); c.braignakEtudier({sujet:'gardien', nouvelle:false});"
    + ' const e=c.braignakEtude; return JSON.stringify({en:!!e});})()'));
  verifier('une étude déjà menée ne fait pas partir Braignak', etudeConnue.en === false, JSON.stringify(etudeConnue));

  // --- 7. choisir DONJON à l'écran-titre arme la map salle serveurs -------
  //     (demande de Patrick : entrer par le donjon = arriver dans la salle
  //     serveurs ; entrer par le village doit la désarmer)
  const choix = JSON.parse(await js(
    '(()=>{const c=window.__webmcpConnexion;'
    + " const don=[...document.querySelectorAll('.entree-tab')].find(b=>/DONJON/i.test(b.innerText));"
    + " const vil=[...document.querySelectorAll('.entree-tab')].find(b=>/VILLAGE/i.test(b.innerText));"
    + " if(!don||!vil) return JSON.stringify({boutons:false});"
    + ' don.onclick(); const apresDonjon = c.MAP_FORCEE;'
    + ' vil.onclick(); const apresVillage = c.MAP_FORCEE;'
    + ' return JSON.stringify({boutons:true, apresDonjon, apresVillage});})()'));
  verifier("les boutons d'entrée existent", choix.boutons === true, 'boutons DONJON/VILLAGE introuvables');
  verifier('choisir DONJON arme la salle serveurs', choix.apresDonjon === 'serveur', 'map = ' + choix.apresDonjon);
  verifier('choisir VILLAGE désarme la salle serveurs', choix.apresVillage === null, 'map = ' + choix.apresVillage);

  // --- 8. LE JEU DÉMARRE VRAIMENT, et on regarde CE QU'IL Y A DEDANS -------
  //     On ne se contente plus de l'état : on démarre la partie par le code
  //     (demarrer) et on inspecte la scène 3D elle-même. C'est la seule façon
  //     de prouver que Braignak et la salle serveurs sont réellement posés.
  const partie = JSON.parse(await js(
    '(()=>{const c=window.__webmcpConnexion;'
    + " const don=[...document.querySelectorAll('.entree-tab')].find(b=>/DONJON/i.test(b.innerText));"
    + ' if(don) don.onclick();'
    + " if(typeof c.demarrer !== 'function') return JSON.stringify({demarre:false, raison:'demarrer absent du pont'});"
    + ' c.demarrer();'
    + " return JSON.stringify({demarre:true, etat:c.etat, map:c.MAP_FORCEE, niveau:c.niveau});})()"));
  verifier('le jeu peut démarrer sans clic', partie.demarre === true, partie.raison || '');
  verifier('la partie est en cours', partie.etat === 'jeu', 'état = ' + partie.etat);
  verifier('on démarre bien avec la map salle serveurs', partie.map === 'serveur', 'map = ' + partie.map);

  await pause(4000);   // le temps que la scène se construise

  const scene3d = JSON.parse(await js(
    '(()=>{const c=window.__webmcpConnexion; const s=c.scene;'
    + " if(!s) return JSON.stringify({scene:false});"
    + " const b = s.getObjectByName('braignak');"
    + ' return JSON.stringify({scene:true, braignakVu:!!b,'
    + '   braignakVisible: !!b && b.visible,'
    + '   morceaux: b ? b.children.length : 0,'
    + '   dansLaScene: !!b && !!b.parent,'
    + "   sallesQuantiques:(c.rooms||[]).filter(r=>r.theme==='quantique').length});})()"));
  verifier('la scène 3D est lisible', scene3d.scene === true, 'scene absente du pont');
  verifier('Braignak est posé dans la scène, retrouvé par son nom',
    scene3d.braignakVu === true && scene3d.dansLaScene === true, JSON.stringify(scene3d));
  verifier('Braignak a bien tous ses morceaux', scene3d.morceaux >= 5,
    scene3d.morceaux + ' morceau(x)');
  verifier('Braignak est visible', scene3d.braignakVisible === true, JSON.stringify(scene3d));
  verifier('la salle serveurs est bien la map jouée', scene3d.sallesQuantiques > 0,
    scene3d.sallesQuantiques + ' salle(s) serveurs');

  ws.close();
} catch (e) {
  verifier('le banc va au bout', false, e.message);
} finally {
  nettoyer();
}

const verts = resultats.filter((r) => r.ok).length;
console.log('\n' + verts + '/' + resultats.length + ' verts');
process.exit(verts === resultats.length ? 0 : 1);
