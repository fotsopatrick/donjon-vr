// cdp-carte.js — preuve « la carte vivante suit Alice en direct ».
// Ouvre le donjon (mission autostart + impulsions « avance ») et la page carte,
// relève à 8 instants PENDANT la marche : position jeu + état de la carte.
// Usage : node cdp-carte.js <port> [out1..out8]
const http = require('http'), fs = require('fs');
const PORT = process.argv[2] || 9249;
const OUTS = process.argv.slice(3);
const wait = (ms) => new Promise(r => setTimeout(r, ms));
const JEU = 'http://127.0.0.1:8099/index.html?mission=1#village';
const CARTE = 'http://127.0.0.1:8002/carte_donjon';

function getJSON(p) { return new Promise((res, rej) => { http.get('http://127.0.0.1:' + PORT + p, r => { let d = ''; r.on('data', c => d += c); r.on('end', () => { try { res(JSON.parse(d)) } catch (e) { rej(e) } }); }).on('error', rej); }); }
function putTab(url) { return new Promise((res, rej) => { const r = http.request({ host: '127.0.0.1', port: PORT, path: '/json/new?' + encodeURIComponent(url), method: 'PUT' }, resp => { let d = ''; resp.on('data', c => d += c); resp.on('end', () => { try { res(JSON.parse(d)) } catch (e) { rej(e) } }); }); r.on('error', rej); r.end(); }); }
async function connect(wsUrl) {
  const ws = new WebSocket(wsUrl); let id = 0; const pend = {};
  const send = (m, p) => new Promise((res, rej) => { const i = ++id; const to = setTimeout(() => { delete pend[i]; rej(new Error('timeout ' + m)); }, 20000); pend[i] = (r) => { clearTimeout(to); res(r); }; ws.send(JSON.stringify({ id: i, method: m, params: p || {} })); });
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
  const posJeu = async () => { const g = await evaluation(jeu, 'D && D.pos ? ({ x: D.pos.x, z: D.pos.z, etat: D.etat, T: D.T, W: D.W, H: D.H, lignes: D.grid.length, cols: (D.grid[0]||[]).length }) : null'); return g; };
  const etatCarte = async () => evaluation(map, 'window.__carte || null');
  const majCarte = async () => { await evaluation(map, 'try{ maj(); "ok" }catch(e){ "err:"+e.message }'); };
  const shot = async (f) => { try { const { data } = await map.send('Page.captureScreenshot', { format: 'png' }); fs.writeFileSync(f, Buffer.from(data, 'base64')); console.log('SHOT', f, fs.statSync(f).size); } catch (e) { console.log('shot échoué', e.message); } };
  const pilote = async (o) => { await evaluation(jeu, 'D.piloter("' + o + '")'); };
  const front = async (sess) => { try { await sess.send('Page.bringToFront'); } catch (e) { } };

  console.log('attente du chargement du jeu (D)…');
  let geo = null;
  for (let i = 0; i < 100; i++) {
    geo = await posJeu();
    if (geo) break;
    if (i % 10 === 9) { const st = await evaluation(jeu, 'document.readyState'); console.log('  … (t' + (i + 1) + '0/300) readyState=' + st); }
    await wait(300);
  }
  if (!geo) { console.log('❌ D introuvable'); process.exit(1); }
  console.log('géométrie T=' + geo.T + ' W=' + geo.W + ' H=' + geo.H + ' lignes=' + geo.lignes + ' cols=' + geo.cols + ' — pos (x,z) ' + Number(geo.x.toFixed(1)) + ',' + Number(geo.z.toFixed(1)));

  console.log('laison 7 s (mission autostart en cours)…');
  await wait(7000);

  const TOURS = ['droite', 'avance', 'gauche', 'avance', 'droite', 'avance'];
  const relev = [];
  for (let i = 0; i < (OUTS.length || 1); i++) {
    await front(jeu);                       // le jeu au premier plan : il marche
    if (TOURS[i]) { await pilote(TOURS[i]); await wait(640); }
    const gp = await posJeu();
    await front(map);                        // la carte au premier plan : capturer
    await majCarte();
    const c = await etatCarte();
    relev.push({ gp, c });
    console.log('RELÈVÉ', (i + 1), '| jeu (x,z) =', Number(gp.x.toFixed(1)) + ',' + Number(gp.z.toFixed(1)),
      '| carte pos', c && c.pos && ('(' + c.pos.x + ',' + c.pos.z + ')'), 'chemin', c && c.chemin, 'dernier', c && c.dernier);
    if (OUTS[i]) await shot(OUTS[i]);
  }

  const positions = relev.filter(r => r.c && r.c.pos).map(r => '(' + r.c.pos.x + ',' + r.c.pos.z + ')');
  const distinct = new Set(positions).size;
  const chemins = relev.map(r => (r.c && r.c.chemin) || 0);
  console.log('CARTE VIVANTE ? positions distinctes : ' + distinct + ' — séquence ' + positions.join(' → '));
  console.log('CHEMIN SUR LA CARTE : ' + chemins.join('→') + (distinct >= 2 ? ' ⇒ SUIVI TEMPS RÉEL : OUI ✅' : ' ⇒ NON ❌'));
  jeu.ws.close(); map.ws.close(); process.exit(0);
})();