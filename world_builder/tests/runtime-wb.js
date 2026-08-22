/* runtime-wb.js — test du runtime Three.js (window.WB) piloté en headless.
   Vérifie : chargement de monde/scene.json, ID porté par l'Object3D,
   déplacement/échelle (transformation seule) et remplacement du GLB.
   Usage : node runtime-wb.js <port CDP> */
const http = require('http');
const PORT = process.argv[2] || 9249;

function getJSON(p) {
  return new Promise((res, rej) => {
    http.get('http://127.0.0.1:' + PORT + p, r => {
      let d = '';
      r.on('data', c => d += c);
      r.on('end', () => { try { res(JSON.parse(d)); } catch (e) { rej(e); } });
    }).on('error', rej);
  });
}

(async () => {
  const pages = await getJSON('/json');
  const page = pages.find(x => x.type === 'page' && x.webSocketDebuggerUrl);
  if (!page) throw new Error('pas de page CDP');
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0;
  const pend = {};
  const send = (m, p) => new Promise(r => { const i = ++id; pend[i] = r; ws.send(JSON.stringify({ id: i, method: m, params: p || {} })); });
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pend[m.id]) { pend[m.id](m.result); delete pend[m.id]; } };
  await new Promise(r => ws.onopen = r);
  await send('Runtime.enable');

  const expr = `(async()=>{
    for(let i=0;i<40 && !(window.WB && window.WB.objets && window.WB.objets.size);i++)
      await new Promise(r=>setTimeout(r,1000));
    const B = window.WB;
    const p = [];
    p.push(['wb_present', !!B]);
    if(!B) return JSON.stringify({tests:p, verdict:'KO'});
    const liste = B.liste();
    p.push(['objets_charges', liste.length >= 2]);
    const un = liste[0];
    const av = B.etat(un.id);
    const d = B.deplace(un.id, 3, 3);
    p.push(['deplace', d.ok && d.position.x===3 && d.position.z===3]);
    const e = B.echelle(un.id, 1.5);
    p.push(['echelle', e.ok && e.echelle===1.5]);
    const r = await B.remplacer(un.id);
    p.push(['remplace_garde_id', r.ok && B.trouver(un.id) && B.trouver(un.id).obj3d.userData.id===un.id]);
    p.push(['version_conservee', B.etat(un.id).assetVersion === av.assetVersion]);
    const ok = p.filter(x=>x[1]!==true).length===0;
    return JSON.stringify({tests:p, verdict: ok?'OK':'KO'});
  })()`;

  const { result } = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
  const r = JSON.parse(result.value);
  for (const [n, ok] of r.tests) console.log(ok ? 'OK    : ' + n : 'ÉCHEC : ' + n);
  console.log('VERDICT', r.verdict);
  ws.close();
  process.exit(r.verdict === 'OK' ? 0 : 1);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
