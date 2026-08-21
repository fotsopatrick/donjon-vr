// SONDE VOL — une seule question : qu'est-ce qui casse quand on passe en vol ?
// Elle ouvre le jeu, écoute les erreurs, met le joueur en vol, et recopie
// la première erreur telle quelle. Usage : node tests/sonde-vol.js [port]
const http = require('http');
const PORT = process.argv[2] || 9247;
const dodo = ms => new Promise(r => setTimeout(r, ms));
const getJSON = p => new Promise((r, j) =>
  http.get('http://127.0.0.1:' + PORT + p, x => { let d = ''; x.on('data', c => d += c); x.on('end', () => { try { r(JSON.parse(d)); } catch (e) { j(e); } }); }).on('error', j));

(async () => {
  const page = (await getJSON('/json')).find(x => x.type === 'page' && x.webSocketDebuggerUrl);
  if (!page) { console.log('AUCUNE PAGE'); process.exit(2); }
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0; const att = {}; const erreurs = [];
  const env = (m, p) => new Promise(r => { const i = ++id; att[i] = r; ws.send(JSON.stringify({ id: i, method: m, params: p || {} })); });
  ws.onmessage = e => {
    const m = JSON.parse(e.data);
    if (m.id && att[m.id]) { att[m.id](m.result || {}); delete att[m.id]; return; }
    if (m.method === 'Runtime.exceptionThrown') {
      const d = m.params.exceptionDetails;
      erreurs.push((d.exception && d.exception.description || d.text || '?').split('\n').slice(0, 3).join(' | '));
    }
    if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error') erreurs.push('LOG: ' + m.params.entry.text);
    if (m.method === 'Inspector.targetCrashed') erreurs.push('LA PAGE A PLANTÉ (renderer mort)');
  };
  await new Promise(r => ws.onopen = r);
  await env('Runtime.enable'); await env('Log.enable'); await env('Page.enable'); await env('Inspector.enable');
  const lire = async x => { const r = await env('Runtime.evaluate', { expression: x, returnByValue: true });
    if (r.exceptionDetails) return 'ERREUR: ' + (r.exceptionDetails.exception && r.exceptionDetails.exception.description || r.exceptionDetails.text);
    return r.result && r.result.value; };

  await env('Page.navigate', { url: 'http://127.0.0.1:8099/index.html?t=' + Date.now() + '' + (process.argv[3] || '#arene') });
  let parti = false;
  for (let i = 0; i < 30 && !parti; i++) {
    await lire('(function(){var b=document.getElementById("jouer");if(b&&!b.disabled)b.click();})()');
    await dodo(1000);
    parti = (await lire('window.D&&window.D.etat')) === 'jeu';
  }
  console.log('jeu démarré :', parti);
  // IMPORTANT : le corps n'est calculé qu'en VUE DE DOS. À la première personne
  // on ne se voit pas, donc rien n'est animé — et la sonde mesurerait du vide.
  for (let i = 0; i < 4 && !(await lire('window.D.avatar && window.D.avatar.visible')); i++) {
    await lire('window.D.basculerVue()'); await dodo(400);
  }
  console.log('vue de dos :', await lire('window.D.avatar.visible'));
  console.log('avant le vol :', await lire('JSON.stringify({vrm:!!(window.D.avatar&&window.D.avatar.userData&&window.D.avatar.userData.vrm),mana:Math.round(window.D.joueur.mana||0)})'));
  erreurs.length = 0;
  console.log('on décolle :', await lire('window.D.joueur.vol=true; window.D.joueur.saut=4; "ok"'));
  await dodo(2500);
  console.log('pendant le vol :', await lire('JSON.stringify({vol:!!window.D.joueur.vol,saut:Math.round((window.D.joueur.saut||0)*10)/10})'));
  if((process.argv[3]||'')==='#village'){
    await dodo(4000);
    console.log('villageois :', await lire('(window.D.villageois||[]).length'));
    console.log('os trouvés  :', await lire('JSON.stringify((window.D.villageois||[]).map(function(v){return v.os?(v.os.trouves||0):-1;}))'));
  }
  console.log('épaule gauche :', await lire('(function(){var v=window.D.avatar.userData.vrm;var b=v.humanoid.getRawBoneNode("leftUpperArm");return b?(b.rotation.x+b.rotation.z):"pas d os";})()'));
  console.log("passages dans la pose en l air :", await lire("window.__poseAir||0"));
  console.log("mixer actif :", await lire("!!window.D.avatar.userData.vrm && true"));
  console.log("\nERREURS VUES :");
  console.log(erreurs.length ? erreurs.slice(0, 6).map(e => '  - ' + e).join('\n') : '  aucune');
  ws.close(); process.exit(0);
})();
