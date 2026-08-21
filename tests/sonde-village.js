// SONDE VILLAGE — une seule question : d'où vient le truc noir sur les épaules ?
// Elle ouvre le village, ATTEND vraiment que les habitants soient posés,
// compte leurs ombres, et prend une photo de près.
// Usage : node tests/sonde-village.js [port]
const http = require('http'), fs = require('fs');
const PORT = process.argv[2] || 9257;
const dodo = ms => new Promise(r => setTimeout(r, ms));
const getJSON = p => new Promise((r, j) =>
  http.get('http://127.0.0.1:' + PORT + p, x => { let d = ''; x.on('data', c => d += c); x.on('end', () => { try { r(JSON.parse(d)); } catch (e) { j(e); } }); }).on('error', j));

(async () => {
  const page = (await getJSON('/json')).find(x => x.type === 'page' && x.webSocketDebuggerUrl);
  if (!page) { console.log('AUCUNE PAGE'); process.exit(2); }
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0; const att = {};
  const env = (m, p) => new Promise(r => { const i = ++id; att[i] = r; ws.send(JSON.stringify({ id: i, method: m, params: p || {} })); });
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && att[m.id]) { att[m.id](m.result || {}); delete att[m.id]; } };
  await new Promise(r => ws.onopen = r);
  await env('Runtime.enable'); await env('Page.enable');
  const lire = async x => { const r = await env('Runtime.evaluate', { expression: x, returnByValue: true });
    if (r.exceptionDetails) return 'ERREUR: ' + (r.exceptionDetails.exception && r.exceptionDetails.exception.description || r.exceptionDetails.text);
    return r.result && r.result.value; };

  await env('Page.navigate', { url: 'http://127.0.0.1:8099/index.html?t=' + Date.now() + '#village' });
  let parti = false;
  for (let i = 0; i < 30 && !parti; i++) {
    await lire('(function(){var b=document.getElementById("jouer");if(b&&!b.disabled)b.click();})()');
    await dodo(1000);
    parti = (await lire('window.D&&window.D.etat')) === 'jeu';
  }
  console.log('jeu démarré :', parti);
  // PATIENCE : les habitants n'apparaissent qu'une fois les gros fichiers arrivés.
  let n = 0;
  for (let i = 0; i < 30 && !n; i++) { await dodo(1500); n = await lire('(window.D.villageois||[]).length'); }
  console.log('habitants posés :', n);
  if (!n) { console.log('AUCUN HABITANT — rien à mesurer'); ws.close(); process.exit(1); }
  await dodo(2000);

  console.log('ombres portées par habitant :', await lire('JSON.stringify((window.D.villageois||[]).map(function(v){var c=0;v.obj.traverse(function(o){if(o.isMesh&&o.castShadow)c++;});return c;}))'));
  console.log('lumières qui font des ombres :', await lire('(function(){var n=0;window.D.scene.traverse(function(o){if(o.isLight&&o.castShadow)n++;});return n;})()'));
  console.log('os trouvés par habitant     :', await lire('JSON.stringify((window.D.villageois||[]).map(function(v){return v.os?(v.os.trouves||0):-1;}))'));
  // De quoi est fait un habitant : noms des morceaux et leur matière
  console.log('morceaux du 1er habitant    :', await lire('(function(){var v=window.D.villageois[0],L=[];v.obj.traverse(function(o){if(o.isMesh)L.push(o.name+"|"+(o.material&&o.material.type)+"|ombre="+(o.castShadow?1:0)+"|visible="+(o.visible?1:0));});return JSON.stringify(L.slice(0,14));})()'));

  // ON SE COLLE À UN HABITANT ET ON PHOTOGRAPHIE
  await lire('(function(){var v=window.D.villageois[0];window.D.joueur.x=v.x+2.2;window.D.joueur.z=v.z+2.2;window.D.joueur.lacet=Math.atan2(-(v.x-window.D.joueur.x),-(v.z-window.D.joueur.z));window.D.joueur.cap=window.D.joueur.lacet;return "ok";})()');
  await dodo(1200);
  const { data } = await env('Page.captureScreenshot', { format: 'png' });
  fs.mkdirSync(__dirname + '/captures', { recursive: true });
  fs.writeFileSync(__dirname + '/captures/villageois_de_pres.png', Buffer.from(data, 'base64'));
  console.log('PHOTO : tests/captures/villageois_de_pres.png');
  ws.close(); process.exit(0);
})();
