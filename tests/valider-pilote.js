// Sonde de validation de la zone pilote : FPS internes (headless) + draw calls
// + triangles + textures + mémoire, aux 4 points demandés, puis les 4 presets
// de ciel avec captures. Usage : node tests/valider-pilote.js <port> <out-prefix>
const http = require('http'), fs = require('fs');
const PORT = process.argv[2] || 9250;
const OUT = process.argv[3] || '/tmp/sky';
const T = 2.6;
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
  const key = async (code, type) => env('Input.dispatchKeyEvent', { type, code, key: code.replace('Key', '').toLowerCase(), windowsVirtualKeyCode: { KeyW: 87 }[code] || 0, nativeVirtualKeyCode: { KeyW: 87 }[code] || 0 });

  await env('Page.navigate', { url: 'http://127.0.0.1:8099/index.html?t=' + Date.now() + '#village' });
  let pret = false;
  for (let i = 0; i < 40; i++) {
    await dodo(1500);
    await ev('(function(){var b=document.getElementById("jouer");if(b&&!b.disabled)b.click()})()');
    if ((await ev('window.D&&window.D.etat')) === 'jeu') { pret = true; break; }
  }
  console.log('PRET=', pret, 'err=', await ev('window.__derniereErreur||"aucune"'));

  const echantillons = async n => {
    const vals = [];
    for (let i = 0; i < n; i++) {
      await dodo(1000);
      const t = (await ev('(document.getElementById("perf")||{}).textContent||""')) || '';
      const m = t.match(/([\d.]+)\s*i\/s/);
      if (m) vals.push(parseFloat(m[1]));
    }
    if (!vals.length) return null;
    return { moy: Math.round(vals.reduce((a, b) => a + b, 0) / vals.length * 10) / 10, min: Math.min(...vals), ech: vals.length };
  };
  const stats = async () => JSON.parse(await ev('(function(){var r=window.D.renderer&&window.D.renderer.info;return JSON.stringify({calls:r&&r.render.calls,tri:r&&r.render.triangles,tex:r&&r.memory.textures,heap:performance.memory?Math.round(performance.memory.usedJSHeapSize/1048576):null})})()'));

  await dodo(3000);
  const s1 = await echantillons(8);
  console.log('SPAWN', JSON.stringify({ fps: s1, stats: await stats() }));
  await ev('window.D.joueur.x=' + (13 * T) + ';window.D.joueur.z=' + (9 * T) + ';1');
  await dodo(2000);
  console.log('PLACE', JSON.stringify({ fps: await echantillons(6), stats: await stats() }));
  await key('KeyW', 'keyDown'); await dodo(400);
  console.log('RUE', JSON.stringify({ fps: await echantillons(6), stats: await stats() }));
  await key('KeyW', 'keyUp');
  await ev('window.D.joueur.x=' + (13 * T) + ';window.D.joueur.z=' + (16 * T) + ';1');
  await dodo(2000);
  console.log('ENTREE', JSON.stringify({ fps: await echantillons(6), stats: await stats() }));

  for (const preset of ['village_golden', 'forest_overcast', 'night_fantasy', 'magical_sky']) {
    await ev('window.SKY&&window.SKY.appliquer("' + preset + '");1');
    await dodo(2500);
    const f = await echantillons(5);
    await dodo(400);
    const { data } = await env('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(OUT + '-' + preset + '.png', Buffer.from(data, 'base64'));
    console.log('SKY', preset, JSON.stringify({ fps: f, stats: await stats() }));
  }
  ws.close(); process.exit(0);
})().catch(e => { console.log('ERR', e.message); process.exit(1); });
