// Vérifie les créatures composant : rat (étage 3) et spectre (étage 4) se
// construisent sans erreur, avec ancrage au sol (boîtes englobantes).
const http = require('http');
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

  await env('Page.navigate', { url: 'http://127.0.0.1:8099/index.html?t=' + Date.now() + '#donjon' });
  let pret = false;
  for (let i = 0; i < 40; i++) {
    await dodo(1500);
    await ev('(function(){var b=document.getElementById("jouer");if(b&&!b.disabled)b.click()})()');
    if ((await ev('window.D&&window.D.etat')) === 'jeu') { pret = true; break; }
  }
  console.log('PRET=', pret, 'err=', await ev('window.__derniereErreur||"aucune"'));

  const audit = () => ev('(function(){var out={};window.D.scene.traverse(o=>{if(o.userData&&o.userData.componentId){var id=o.userData.componentId;out[id]=(out[id]||0)+1;}});var boites=[];window.D.ennemis.forEach(e=>{if(e.obj){var b=new window.D.THREE.Box3().setFromObject(e.obj);boites.push({type:e.type,yMin:+b.min.y.toFixed(2),yMax:+b.max.y.toFixed(2)});}});return JSON.stringify({composants:out,boites:boites});})()');

  await ev('window.D.allerA(3);1');   // clairière : rats
  await dodo(2500);
  console.log('ETAGE3 err=', await ev('window.__derniereErreur||"aucune"'));
  console.log('ETAGE3', await audit());

  await ev('window.D.allerA(4);1');   // voile : spectres
  await dodo(2500);
  console.log('ETAGE4 err=', await ev('window.__derniereErreur||"aucune"'));
  console.log('ETAGE4', await audit());

  ws.close(); process.exit(0);
})().catch(e => { console.log('ERR', e.message); process.exit(1); });
