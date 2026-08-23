// Audit PHASE B — erreurs + compteurs par map (contre la baseline).
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
  await env('Page.navigate', { url: 'http://127.0.0.1:8099/index.html?t=' + Date.now() + '#village' });
  for (let i = 0; i < 40; i++) { await dodo(1500); await ev('(function(){var b=document.getElementById("jouer");if(b&&!b.disabled)b.click()})()'); if ((await ev('window.D&&window.D.etat')) === 'jeu') break; }
  const check = async nom => {
    await dodo(2500);
    const perf = (await ev('(document.getElementById("perf")||{}).textContent')) || '';
    const calls = await ev('window.D.renderer&&window.D.renderer.info.render.calls');
    console.log(nom, '| err=', await ev('window.__derniereErreur||"aucune"'),
                '| calls=', calls, '|', perf.replace(/·.*v22/, '').trim());
  };
  await check('VILLAGE   ');
  for (let n = 1; n <= 5; n++){ await ev('window.D.allerA(' + n + ');1'); await check('DONJON é.' + n + ' '); }
  await ev('window.D.allerA(-1);1'); await check('ARENE     ');
  ws.close(); process.exit(0);
})().catch(e => { console.log('ERR', e.message); process.exit(1); });
