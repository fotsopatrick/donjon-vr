// Captures d'inspection reproductibles (Phase A) — CDP.
// Pour chaque point de window.INSPECTION, téléporte + oriente + capture dans
// tests/captures/inspection/<id>.png (1600×1000, FOV/exposition du jeu fixes),
// puis génère la planche tests/captures/inspection/index.html.
const http = require('http'), fs = require('fs'), path = require('path');
const PORT = process.argv[2] || 9250;
const OUTDIR = path.join(__dirname, 'captures', 'inspection');
const BASE = 'http://127.0.0.1:8099/index.html';
fs.mkdirSync(OUTDIR, { recursive: true });
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
  const shot = async id => { const { data } = await env('Page.captureScreenshot', { format: 'png' }); fs.writeFileSync(path.join(OUTDIR, id + '.png'), Buffer.from(data, 'base64')); };

  await env('Page.navigate', { url: BASE + '?t=' + Date.now() + '#village' });
  let pret = false;
  for (let i = 0; i < 50; i++) {
    await dodo(1200);
    if (await ev('!!window.INSPECTION')) { pret = true; break; }
  }
  console.log('INSPECTION chargée =', pret);
  const pts = await ev('JSON.stringify(window.INSPECTION.points)');
  const points = JSON.parse(pts);

  // 1) le titre, AVANT de lancer le jeu
  const titre = points.find(p => p.ui === 'titre');
  await dodo(2000);
  if (titre){ await shot(titre.id); console.log('capture', titre.id, '—', titre.nom); }

  // 2) on lance le jeu
  await ev('(function(){var b=document.getElementById("jouer");if(b&&!b.disabled)b.click()})()');
  for (let i = 0; i < 30; i++) { await dodo(1000); if ((await ev('window.D&&window.D.etat')) === 'jeu') break; }
  console.log('etat =', await ev('window.D&&window.D.etat'));

  // 3) les points du monde (sauf le titre déjà fait)
  for (const pt of points){
    if (pt.ui === 'titre') continue;
    if (pt.id === 'u-titre') continue;
    if (pt.ui === 'hud' || pt.ui === 'pause') continue;   // traités à part
    await ev('window.INSPECTION.aller(' + JSON.stringify(pt) + ');1');
    await dodo(3500);                                    // laisse le rendu se poser
    await shot(pt.id);
    console.log('capture', pt.id, '—', pt.nom);
  }

  // 4) HUD en jeu (capture normale, HUD visible)
  const hud = points.find(p => p.ui === 'hud');
  if (hud){ await ev('window.INSPECTION.aller(' + JSON.stringify(points.find(p => p.id === '01-spawn')) + ');1'); await dodo(3000); await shot(hud.id); console.log('capture', hud.id); }
  // 5) pause
  const pause = points.find(p => p.ui === 'pause');
  if (pause){ await ev('window.INSPECTION.aller(' + JSON.stringify(pause) + ');1'); await dodo(2500); await shot(pause.id); console.log('capture', pause.id); await ev('window.D.reprendreJeu&&window.D.reprendreJeu();1'); }

  // 6) la planche / contact sheet
  let html = '<!doctype html><html lang="fr"><head><meta charset="utf-8">' +
    '<title>Inspection — planche des captures</title>' +
    '<style>body{background:#0a0908;color:#e8dcc0;font-family:Georgia,serif;margin:0;padding:20px}' +
    'h1{font-size:18px;letter-spacing:.2em;color:#e8b661;text-transform:uppercase}' +
    '.groupe{margin:26px 0 8px;font-size:13px;letter-spacing:.16em;color:#8f9ec0;text-transform:uppercase;border-bottom:1px solid rgba(196,148,80,.3);padding-bottom:4px}' +
    '.grille{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px;margin-bottom:30px}' +
    '.carte{background:#141009;border:1px solid rgba(196,148,80,.25);border-radius:4px;overflow:hidden}' +
    '.carte img{width:100%;display:block;aspect-ratio:16/10;object-fit:cover}' +
    '.carte .leg{border-top:1px solid rgba(196,148,80,.2);padding:6px 10px;font-size:12px}' +
    '.carte .leg b{color:#ffe4ae;font-weight:400}' +
    '.carte .leg span{color:#8a7c62;display:block;font-size:11px;margin-top:2px}</style></head><body>';
  html += '<h1>Planche d\'inspection — captures reproductibles</h1>';
  let cat = '';
  for (const pt of points){
    if (pt.cat !== cat){ cat = pt.cat; html += '<div class="groupe">' + cat + '</div><div class="grille">'; }
    html += '<div class="carte"><img src="' + pt.id + '.png" alt="' + pt.id + '">' +
            '<div class="leg"><b>' + pt.id + ' — ' + pt.nom + '</b>' +
            (pt.note ? '<span>' + pt.note + '</span>' : '') + '</div></div>';
  }
  html += '</div></body></html>';
  fs.writeFileSync(path.join(OUTDIR, 'index.html'), html);
  console.log('planche :', path.join(OUTDIR, 'index.html'));
  console.log('erreur jeu =', await ev('window.__derniereErreur||"aucune"'));
  ws.close(); process.exit(0);
})().catch(e => { console.log('ERR', e.message); process.exit(1); });
