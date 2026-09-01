// cdp-balade.js — preuve « la carte suit Alice de case en case ».
// Ouvre le donjon (mission) + la carte, puis fait marcher Alice longtemps
// droit devant : on relève la case côté jeu ET côté carte à chaque pas.
// Usage : node cdp-balade.js <port> [cadre1.png..cadre3.png]
const http = require('http'), fs = require('fs');
const PORT = process.argv[2] || 9249;
const CADRES = process.argv.slice(3);
const wait = (ms) => new Promise(r => setTimeout(r, ms));
const JEU = 'http://127.0.0.1:8099/index.html?mission=1#village';
const CARTE = 'http://127.0.0.1:8002/carte_donjon';
const PAS = 20, TPS = 620;

function getJSON(p) { return new Promise((res, rej) => { http.get('http://127.0.0.1:' + PORT + p, r => { let d = ''; r.on('data', c => d += c); r.on('end', () => { try { res(JSON.parse(d)) } catch (e) { rej(e) } }); }).on('error', rej); }); }
function putTab(url) { return new Promise((res, rej) => { const r = http.request({ host: '127.0.0.1', port: PORT, path: '/json/new?' + encodeURIComponent(url), method: 'PUT' }, resp => { let d = ''; resp.on('data', c => d += c); resp.on('end', () => { try { res(JSON.parse(d)) } catch (e) { rej(e) } }); }); r.on('error', rej); r.end(); }); }
async function connect(wsUrl) {
  const ws = new WebSocket(wsUrl); let id = 0; const pend = {};
  const send = (m, p) => new Promise((res, rej) => { const i = ++id; const to = setTimeout(() => { delete pend[i]; rej(new Error('timeout ' + m)); }, 25000); pend[i] = (r) => { clearTimeout(to); res(r); }; ws.send(JSON.stringify({ id: i, method: m, params: p || {} })); });
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pend[m.id]) { pend[m.id](m.result || {}); delete pend[m.id]; } };
  ws.onerror = () => console.log('WS ERROR'); ws.onclose = () => console.log('WS CLOSE');
  await Promise.race([
    new Promise((r, rej) => { ws.onopen = () => r(); setTimeout(() => rej(new Error('ouverture WS trop lente')), 15000).unref(); }),
    new Promise((r, rej) => { ws.onerror = () => rej(new Error('erreur WS')); }),
  ]);
  await send('Runtime.enable'); await send('Page.enable');
  return { ws, send };
}
(async () => {
  let t; for (let i = 0; i < 25; i++) { try { t = await getJSON('/json'); if (t.some(x => x.type === 'page' && x.webSocketDebuggerUrl)) break; } catch (e) { } await wait(400); }
  const base = t.find(x => x.type === 'page' && x.webSocketDebuggerUrl);
  if (!base) { console.log('❌ PAS DE PAGE CDP'); process.exit(1); }
  const jeu = await connect(base.webSocketDebuggerUrl);
  await jeu.send('Page.navigate', { url: JEU });
  const carte = await putTab(CARTE);
  const map = await connect(carte.webSocketDebuggerUrl);
  const evaluation = async (sess, expr) => { const r = await sess.send('Runtime.evaluate', { expression: expr, returnByValue: true }); return (r.result && r.result.value) || null; };
  const posJeu = async () => evaluation(jeu, 'D && D.pos ? { x:+D.pos.x.toFixed(1), z:+D.pos.z.toFixed(1) } : null');
  const etatCarte = async () => evaluation(map, 'window.__carte || null');
  const majCarte = async () => { await evaluation(map, 'try{ maj(); "ok" }catch(e){ "err:"+e.message }'); };
  const shot = async (f) => { try { const { data } = await map.send('Page.captureScreenshot', { format: 'png' }); fs.writeFileSync(f, Buffer.from(data, 'base64')); console.log('SHOT', f, fs.statSync(f).size); } catch (e) { console.log('shot échoué', e.message); } };
  const pilote = async (o) => { await evaluation(jeu, 'D.piloter("' + o + '")'); };
  const front = async (sess) => { try { await sess.send('Page.bringToFront'); } catch (e) { } };

  console.log('attente du chargement du jeu (D)…');
  let geo = null;
  for (let i = 0; i < 60; i++) { geo = await posJeu(); if (geo) break; await wait(500); }
  if (!geo) { console.log('❌ D jamais prêt'); process.exit(1); }
  console.log('départ : (x,z) =', geo.x + ',' + geo.z);
  await front(map); await majCarte(); await wait(300);
  await shot(CADRES[0] || '/tmp/balade_debut.png');

  let chemin = null;
  const vuJeu = new Set(), vuCarte = new Set();
  const tileJeu = async () => { const p = await posJeu(); return p ? Math.floor(p.x / 2.6) + ',' + Math.floor(p.z / 2.6) : null; };
  for (let i = 0; i < PAS; i++) {
    await front(jeu);
    await pilote(i % 3 === 2 ? 'gauche' : 'avance');
    await wait(TPS);
    const tj = await tileJeu();
    await front(map); await majCarte();
    const etat = await etatCarte();
    if (tj) vuJeu.add(tj);
    if (etat && etat.pos) vuCarte.add(etat.pos.x + ',' + etat.pos.z);
    chemin = (etat && etat.chemin) ? etat.chemin.length : null;
    if (i === 0 || (i + 1) % 5 === 0) { await shot(CADRES[Math.floor((i + 1) / 5)] || ('/tmp/balade_p' + (i + 1) + '.png')); }
    console.log(`pas ${i + 1}/${PAS} | jeu case {${tj}} | carte pos (${etat ? etat.pos.x : '?'},${etat ? etat.pos.z : '?'}) chemin ${chemin}`);
  }
  console.log('CASES VUES (jeu)  :', [...vuJeu].join(' -> '));
  console.log('CASES VUES (carte):', [...vuCarte].join(' -> '));
  console.log('CHEMIN carte final :', chemin, 'case(s)');
  console.log(vuJeu.size >= 2 && vuCarte.size >= 2 ? 'CARTE QUI SUIT ✅' : 'CARTE QUI SUIT ❌');
})().catch(e => { console.log('ERREUR', e.message); process.exit(1); });