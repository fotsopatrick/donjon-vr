// Vérifie la route village→donjon : la rue vers le second village ne déclenche
// PAS la descente, et l'entrée (11,25) déclenche bien la descente. Capture l'approche.
const http = require('http'), fs = require('fs');
const PORT = process.argv[2] || 9250;
const gj = p => new Promise((r, j) => http.get('http://127.0.0.1:' + PORT + p, x => { let d = ''; x.on('data', c => d += c); x.on('end', () => { try { r(JSON.parse(d)) } catch (e) { j(e) } }); }).on('error', j));
const dodo = ms => new Promise(r => setTimeout(r, ms));
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
  const niv = () => ev('window.KOTOAGE&&window.KOTOAGE.niveau');
  console.log('PRET=', pret, 'niveau=', await niv(), 'err=', await ev('window.__derniereErreur||"aucune"'));

  // 1) la rue vers le second village ne doit PAS faire descendre
  await ev('window.D.joueur.x=' + (13 * 2.6) + ';window.D.joueur.z=' + (30 * 2.6) + ';1');
  await dodo(2500);
  console.log('RUE (13,30) niveau=', await niv(), '(attendu 0)');

  // 2) l'entrée (11,25) doit faire descendre
  await ev('window.D.joueur.x=' + (11 * 2.6 + 1.3) + ';window.D.joueur.z=' + (25 * 2.6 + 1.3) + ';1');
  await dodo(3000);
  console.log('ENTREE (11,25) niveau=', await niv(), '(attendu 1)');

  // 3) on remonte au village et on capture l'approche (joueur au coude, regard vers l'entrée)
  await ev('window.D.allerA(0);1');
  await dodo(1500);
  await ev('window.D.joueur.x=' + (11 * 2.6) + ';window.D.joueur.z=' + (22.6 * 2.6) + ';window.D.joueur.lacet=' + Math.PI + ';1');
  await dodo(2500);
  const { data } = await env('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('/home/orel/donjon-vr/tests/captures/route-approche.png', Buffer.from(data, 'base64'));
  console.log('CAPTURE approche OK');

  ws.close(); process.exit(0);
})().catch(e => { console.log('ERR', e.message); process.exit(1); });
