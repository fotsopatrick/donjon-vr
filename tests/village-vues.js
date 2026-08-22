// Validation runtime du village (§18) : 8 points de vue + erreurs + compteurs.
const http = require('http'), fs = require('fs');
const PORT = process.argv[2] || 9250;
const T = 2.6;
const gj = p => new Promise((r, j) => http.get('http://127.0.0.1:' + PORT + p, x => { let d = ''; x.on('data', c => d += c); x.on('end', () => { try { r(JSON.parse(d)) } catch (e) { j(e) } }); }).on('error', j));
const dodo = ms => new Promise(r => setTimeout(r, ms));
const VUES = [
  ['place',       13,  9, 0],
  ['rue',         13, 13, 3.14],
  ['sortie',      13, 18, 3.14],
  ['route-donjon',13, 22.6, -1.5],
  ['entree',      10.6,24.5, 3.14],
  ['second-village',13,46, 3.14],
  ['ferme',        6, 6.5, 3.14],
];
(async () => {
  const page = (await gj('/json')).find(x => x.type === 'page' && x.webSocketDebuggerUrl);
  const ws = new WebSocket(page.webSocketDebuggerUrl); let id = 0; const a = {};
  const env = (m, p) => new Promise(r => { const i = ++id; a[i] = r; ws.send(JSON.stringify({ id: i, method: m, params: p || {} })) });
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && a[m.id]) { a[m.id](m.result || {}); delete a[m.id] } };
  await new Promise(r => ws.onopen = r);
  await env('Runtime.enable'); await env('Page.enable');
  const ev = async x => { const r = await env('Runtime.evaluate', { expression: x, returnByValue: true }); return r.result && r.result.value };

  await env('Page.navigate', { url: 'http://127.0.0.1:8099/index.html?t=' + Date.now() + '#village' });
  let pret = false;
  for (let i = 0; i < 40; i++) {
    await dodo(1500);
    await ev('(function(){var b=document.getElementById("jouer");if(b&&!b.disabled)b.click()})()');
    if ((await ev('window.D&&window.D.etat')) === 'jeu') { pret = true; break; }
  }
  console.log('PRET=', pret);
  for (const [nom, tx, tz, lacet] of VUES) {
    await ev('window.D.joueur.vol=false;window.D.joueur.saut=0;window.D.joueur.x=' + (tx * T) + ';window.D.joueur.z=' + (tz * T) + ';window.D.joueur.lacet=' + lacet + ';1');
    await dodo(3000);
    const err = await ev('window.__derniereErreur||"aucune"');
    const { data } = await env('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync('/home/orel/donjon-vr/tests/captures/village-' + nom + '.png', Buffer.from(data, 'base64'));
    console.log(nom, 'err=', err);
  }
  // vue aérienne
  await ev('window.D.joueur.vol=true;window.D.joueur.saut=35;window.D.joueur.x=' + (13 * T) + ';window.D.joueur.z=' + (9 * T) + ';window.D.joueur.lacet=3.14;window.D.joueur.tangage=-0.6;1');
  await dodo(2500);
  const { data } = await env('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('/home/orel/donjon-vr/tests/captures/village-aerien.png', Buffer.from(data, 'base64'));
  console.log('aerien err=', await ev('window.__derniereErreur||"aucune"'));
  console.log('perf=', await ev('(document.getElementById("perf")||{}).textContent'));
  ws.close(); process.exit(0);
})().catch(e => { console.log('ERR', e.message); process.exit(1); });
