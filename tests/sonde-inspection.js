// SONDE INSPECTION (touche E) — une seule question : près d'un bâtiment du
// world builder, l'indice [E] Examiner apparaît et E ouvre la fiche de l'objet,
// sans casser l'interaction E (fiche du joueur sinon).
// Usage : node tests/sonde-inspection.js [port]
const http = require('http'), fs = require('fs');
const PORT = process.argv[2] || 9259;
const dodo = ms => new Promise(r => setTimeout(r, ms));
const getJSON = p => new Promise((r, j) =>
  http.get('http://127.0.0.1:' + PORT + p, x => { let d = ''; x.on('data', c => d += c); x.on('end', () => { try { r(JSON.parse(d)); } catch (e) { j(e); } }); }).on('error', j));

let echecs = 0;
const verifie = (nom, cond, detail) => {
  console.log((cond ? '  OK  ' : '  ÉCHEC ') + nom + (cond ? '' : ' — ' + (detail || '? ')));
  if (!cond) echecs++;
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
  const lire = async x => { const r = await env('Runtime.evaluate', { expression: x, returnByValue: true });
    if (r.exceptionDetails) return 'ERREUR: ' + (r.exceptionDetails.exception && r.exceptionDetails.exception.description || r.exceptionDetails.text);
    return r.result && r.result.value; };
  const appuyerE = () => lire('window.dispatchEvent(new KeyboardEvent("keydown",{code:"KeyE",key:"e",bubbles:true,cancelable:true}))');

  await env('Page.navigate', { url: 'http://127.0.0.1:8099/index.html?t=' + Date.now() + '#village' });
  let modulePret = false;
  for (let i = 0; i < 90 && !modulePret; i++) { await dodo(1000); modulePret = !!(await lire('!!(window.KOTOAGE && window.WB)')); }
  verifie('module jeu prêt (KOTOAGE + WB)', modulePret);
  let parti = false;
  for (let i = 0; i < 40 && !parti; i++) {
    await lire('(function(){var b=document.getElementById("jouer");if(b&&!b.disabled)b.click();})()');
    await dodo(1000);
    parti = (await lire('window.D&&window.D.etat')) === 'jeu';
  }
  verifie('jeu démarré au hameau', parti);
  for (let i = 0; i < 20 && (await lire('window.WB.objets.size')) !== 3; i++) await dodo(1000);
  verifie('3 bâtiments du world builder posés', (await lire('window.WB.objets.size')) === 3, 'vu ' + await lire('window.WB.objets.size'));

  // 1) loin des objets : pas d'indice
  await lire('window.D.joueur.x = 30; window.D.joueur.z = 30;');
  await dodo(1200);
  verifie('loin : pas d\'indice [E] Examiner', (await lire('document.getElementById("hint-examiner").classList.contains("on")')) === false);
  verifie('loin : aucun objet à portée', (await lire('!!window.D.objetProche()')) === false);

  // 2) à côté du bâtiment building_001 (maison nordique, posé en -6, 8) : l'indice s'allume
  await lire('window.D.joueur.x = -6; window.D.joueur.z = 8;');
  await dodo(1200);
  const proche = await lire('window.D.objetProche() ? window.D.objetProche().etat.id : null');
  verifie('près de building_001 : objet détecté', proche === 'building_001', 'vu ' + proche);
  const indice = await lire('document.getElementById("hint-examiner").textContent');
  verifie('indice affiché avec le nom', /\[E\] Examiner — Maison nordique/.test(indice), 'indice : « ' + indice + ' »');

  // 3) E ouvre la fiche de l'objet
  await appuyerE(); await dodo(600);
  verifie('E ouvre la fiche de l\'objet', (await lire('window.D.ficheObjetOuvert')) === true);
  verifie('la fiche de l\'objet est visible (mesh)', (await lire('window.D && window.D.ficheObjetOuvert')) === true);
  // E referme
  await appuyerE(); await dodo(400);
  verifie('E referme la fiche', (await lire('window.D.ficheObjetOuvert')) === false);

  // 4) loin des objets, E ouvre la fiche du JOUEUR (comportement E existant)
  await lire('window.D.joueur.x = 30; window.D.joueur.z = 30;');
  await dodo(1000);
  await appuyerE(); await dodo(400);
  verifie('loin : E ouvre la fiche du joueur (statut)', (await lire('window.D.statutOuvert')) === true);

  verifie('aucune erreur écran', (await lire('!document.getElementById("boite-erreur")')) === true);

  const { data } = await env('Page.captureScreenshot', { format: 'png' });
  fs.mkdirSync(__dirname + '/captures', { recursive: true });
  fs.writeFileSync(__dirname + '/captures/inspection_E.png', Buffer.from(data, 'base64'));
  console.log('PHOTO : tests/captures/inspection_E.png');

  ws.close();
  console.log(echecs ? 'Résultat : ' + echecs + ' échec(s)' : 'Résultat : 0 échec');
  process.exit(echecs ? 1 : 0);
})();
