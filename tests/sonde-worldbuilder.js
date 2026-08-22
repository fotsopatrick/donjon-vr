// SONDE WORLD-BUILDER — une seule question : l'UI de construction (P0.5)
// se charge-t-elle et fonctionne-t-elle dans le VRAI jeu ?
// Vérifie : expositions (camera/renderer), window.WB + ses objets posés,
// bouton « Construire (B) », bascule du mode constructeur, absence d'erreur.
// Usage : node tests/sonde-worldbuilder.js [port]
const http = require('http'), fs = require('fs');
const PORT = process.argv[2] || 9258;
const dodo = ms => new Promise(r => setTimeout(r, ms));
const getJSON = p => new Promise((r, j) =>
  http.get('http://127.0.0.1:' + PORT + p, x => { let d = ''; x.on('data', c => d += c); x.on('end', () => { try { r(JSON.parse(d)); } catch (e) { j(e); } }); }).on('error', j));

let echecs = 0;
const verifie = (nom, cond, detail) => {
  console.log((cond ? '  OK  ' : '  ÉCHEC ') + nom + (cond ? '' : ' — ' + (detail || '? ')));
  if (!cond) echecs++;
};
const erreursConsole = [];
const consoleMsg = m => {
  if (m.type !== 'error') return;
  erreursConsole.push((m.args || []).map(a => a.value !== undefined ? a.value : (a.description || a.type)).join(' '));
};

(async () => {
  const page = (await getJSON('/json')).find(x => x.type === 'page' && x.webSocketDebuggerUrl);
  if (!page) { console.log('AUCUNE PAGE'); process.exit(2); }
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0; const att = {};
  const env = (m, p) => new Promise(r => { const i = ++id; att[i] = r; ws.send(JSON.stringify({ id: i, method: m, params: p || {} })); });
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && att[m.id]) { att[m.id](m.result || {}); delete att[m.id]; } };
  await new Promise(r => ws.onopen = r);
  await env('Runtime.enable'); await env('Page.enable');
  const guard = m => { try { if (m.method === 'Runtime.consoleAPICalled') consoleMsg(m.params); } catch (e) {} };
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && att[m.id]) { att[m.id](m.result || {}); delete att[m.id]; } else guard(m); };
  const lire = async x => { const r = await env('Runtime.evaluate', { expression: x, returnByValue: true });
    if (r.exceptionDetails) return 'ERREUR: ' + (r.exceptionDetails.exception && r.exceptionDetails.exception.description || r.exceptionDetails.text);
    return r.result && r.result.value; };

  await env('Page.navigate', { url: 'http://127.0.0.1:8099/index.html?t=' + Date.now() + '#village' });
  // PATIENCE : le module du jeu (gros fichier + imports Three) met du temps à
  // s'évaluer sur nomi en rendu logiciel. On attend window.KOTOAGE avant tout.
  let modulePret = false;
  for (let i = 0; i < 90 && !modulePret; i++) { await dodo(1000); modulePret = !!(await lire('!!(window.KOTOAGE && window.WB)')); }
  console.log('module jeu prêt :', modulePret);
  let parti = false;
  for (let i = 0; i < 40 && !parti; i++) {
    await lire('(function(){var b=document.getElementById("jouer");if(b&&!b.disabled)b.click();})()');
    await dodo(1000);
    parti = (await lire('window.D&&window.D.etat')) === 'jeu';
  }
  console.log('jeu démarré :', parti);
  if (!modulePret || !parti) {
    console.log('DIAGNOSTIC :');
    console.log('  window.D          :', await lire('typeof window.D'));
    console.log('  window.KOTOAGE    :', await lire('typeof window.KOTOAGE'));
    console.log('  window.WB         :', await lire('typeof window.WB'));
    console.log('  readyState        :', await lire('document.readyState'));
    console.log('  bouton jouer      :', await lire('(function(){var b=document.getElementById("jouer");return b?{trouve:true,disabled:b.disabled,affich:getComputedStyle(b).display}:{trouve:false};})()'));
    console.log('  boite-erreur      :', await lire('(function(){var b=document.getElementById("boite-erreur");return b?b.textContent.slice(0,400):"absente";})()'));
    console.log('  dernières ress.   :', await lire('JSON.stringify(performance.getEntriesByType("resource").slice(-8).map(function(e){return e.name.split("/").pop()+" ("+Math.round(e.duration)+"ms)";}))'));
    console.log('  module scripts    :', await lire('JSON.stringify(Array.from(document.scripts).map(function(s){return s.src.split("/").pop()||"(inline)";}))'));
  }
  console.log('erreurs console     :', erreursConsole.length ? erreursConsole.slice(0,5) : 'aucune');

  // PATIENCE : le WB charge ses GLB dès le chargement, l'UI aussi.
  let wbPret = false;
  for (let i = 0; i < 20 && !wbPret; i++) { await dodo(1000); wbPret = !!(await lire('!!window.WB && !!window.KOTOAGE')); }
  verifie('world-builder.js chargé (window.WB)', wbPret);

  verifie('KOTOAGE expose camera', !!(await lire('!!(window.KOTOAGE&&window.KOTOAGE.camera)')), 'camera manquante');
  verifie('KOTOAGE expose renderer', !!(await lire('!!(window.KOTOAGE&&window.KOTOAGE.renderer)')), 'renderer manquant');
  verifie('UI : bouton « Construire (B) » présent', !!(await lire('!!document.getElementById("wbui-bouton")')));
  verifie('UI : panneau présent', !!(await lire('!!document.getElementById("wbui-panneau")')));
  verifie('UI : panneau caché au départ', (await lire('document.getElementById("wbui-panneau").classList.contains("cache")')) === true);

  const nObjets = await lire('window.WB ? window.WB.objets.size : -1');
  verifie('WB : objets du hameau posés (scene.json)', nObjets === 3, 'vu ' + nObjets + ' objets (attendu 3)');

  // Appui sur B → mode constructeur
  await lire('document.dispatchEvent(new KeyboardEvent("keydown",{code:"KeyB",bubbles:true,cancelable:true}))');
  await dodo(400);
  const actif = await lire('window.WBUI && window.WBUI.enModeConstructeur');
  verifie('B active le mode constructeur (WBUI.enModeConstructeur)', actif === true, 'vu ' + actif);
  verifie('panneau visible en mode constructeur', (await lire('document.getElementById("wbui-panneau").classList.contains("cache")')) === false);
  // GARDE-FOU : en mode constructeur, un clic sur le terrain ne doit PAS frapper
  // (le world builder gère le clic). On mesure l'observable atkCd : 0 en mode
  // constructeur, > 0 dès qu'on est sorti du mode (le jeu a repris la main).
  const cliquerCanvas = '(()=>{const c=window.KOTOAGE.renderer.domElement;const o={button:0,clientX:400,clientY:300,bubbles:true,cancelable:true};c.dispatchEvent(new MouseEvent("mousedown",o));c.dispatchEvent(new MouseEvent("click",o));return "ok";})()';
  await lire('window.D.joueur.atkCd = 0');
  await lire(cliquerCanvas);
  await dodo(200);
  const atkConstructeur = await lire('window.D.joueur.atkCd');
  verifie('mode constructeur : clic ne frappe PAS (atkCd 0)', atkConstructeur === 0, 'atkCd = ' + atkConstructeur);

  // Second B → on quitte
  await lire('document.dispatchEvent(new KeyboardEvent("keydown",{code:"KeyB",bubbles:true,cancelable:true}))');
  await dodo(300);
  verifie('B re-quitte le mode constructeur', (await lire('window.WBUI && window.WBUI.enModeConstructeur')) === false);
  // témoin : hors mode constructeur, le même clic frappe bien (atkCd > 0)
  await lire('window.D.joueur.atkCd = 0');
  await lire(cliquerCanvas);
  await dodo(200);
  const atkNormal = await lire('window.D.joueur.atkCd');
  verifie('témoin : hors mode, le clic frappe bien (atkCd > 0)', atkNormal > 0, 'atkCd = ' + atkNormal);

  verifie('aucune erreur écran (boite-erreur absente)', (await lire('!document.getElementById("boite-erreur")')) === true);

  const { data } = await env('Page.captureScreenshot', { format: 'png' });
  fs.mkdirSync(__dirname + '/captures', { recursive: true });
  fs.writeFileSync(__dirname + '/captures/worldbuilder_ui.png', Buffer.from(data, 'base64'));
  console.log('PHOTO : tests/captures/worldbuilder_ui.png');

  ws.close();
  console.log(echecs ? 'Résultat : ' + echecs + ' échec(s)' : 'Résultat : 0 échec');
  process.exit(echecs ? 1 : 0);
})();
