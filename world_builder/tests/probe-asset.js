/* probe-asset.js — vérifie qu'un asset précis est réellement chargé dans
   Three.js par world-builder.js (window.WB).
   Usage : node probe-asset.js <port CDP> <assetId> */
const http = require('http');
const PORT = process.argv[2] || 9249;
const ID = process.argv[3];
if (!ID) { console.error('usage: node probe-asset.js <port> <assetId>'); process.exit(2); }

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
    for(let i=0;i<60 && !(window.WB && window.WB.objets && window.WB.objets.size);i++)
      await new Promise(r=>setTimeout(r,1000));
    if(!window.WB) return JSON.stringify({present:false, raisons:['WB absent']});
    const liste = window.WB.liste();
    const cible = liste.find(o=>o.id==='${ID}');
    const obj = window.WB.trouver('${ID}');
    return JSON.stringify({
      present: !!cible,
      presentDansLaListe: !!cible,
      id3d: obj && obj.obj3d.userData.id,
      version: cible && cible.version,
      position: cible && cible.position,
      nbObjetsCharges: liste.length,
      ids: liste.map(o=>o.id)
    });
  })()`;

  const { result } = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
  const r = JSON.parse(result.value);
  console.log('PRESENT', r.present ? 'OUI' : 'NON');
  console.log('details', JSON.stringify(r, null, 1));
  ws.close();
  process.exit(r.present ? 0 : 1);
})().catch(e => { console.error('ERR', e.message); process.exit(1); });
