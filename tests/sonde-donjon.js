// SONDE DONJON — une seule question : depuis l'endroit où on arrive,
// peut-on VRAIMENT marcher jusqu'à la sortie de l'étage ?
// Elle remplit la carte de proche en proche (comme de l'eau qui coule) et dit
// si la case de sortie est mouillée. Usage : node tests/sonde-donjon.js [port] [etage]
const http = require('http'), fs = require('fs');
const PORT = process.argv[2] || 9262;
const ETAGE = +(process.argv[3] || 1);
const dodo = ms => new Promise(r => setTimeout(r, ms));
const getJSON = p => new Promise((r, j) =>
  http.get('http://127.0.0.1:' + PORT + p, x => { let d=''; x.on('data',c=>d+=c); x.on('end',()=>{ try{ r(JSON.parse(d)); }catch(e){ j(e); } }); }).on('error', j));

(async () => {
  const page = (await getJSON('/json')).find(x => x.type === 'page' && x.webSocketDebuggerUrl);
  if (!page) { console.log('AUCUNE PAGE'); process.exit(2); }
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0; const att = {};
  const env = (m,p) => new Promise(r => { const i = ++id; att[i]=r; ws.send(JSON.stringify({id:i, method:m, params:p||{}})); });
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && att[m.id]) { att[m.id](m.result||{}); delete att[m.id]; } };
  await new Promise(r => ws.onopen = r);
  await env('Runtime.enable'); await env('Page.enable');
  const lire = async x => { const r = await env('Runtime.evaluate', {expression:x, returnByValue:true});
    if (r.exceptionDetails) return 'ERREUR: ' + (r.exceptionDetails.exception && r.exceptionDetails.exception.description || r.exceptionDetails.text);
    return r.result && r.result.value; };

  await env('Page.navigate', { url:'http://127.0.0.1:8099/index.html?t=' + Date.now() + '#donjon' });
  let parti = false;
  for (let i=0;i<30 && !parti;i++){
    await lire('(function(){var b=document.getElementById("jouer");if(b&&!b.disabled)b.click();})()');
    await dodo(1000);
    parti = (await lire('window.D&&window.D.etat')) === 'jeu';
  }
  console.log('jeu démarré :', parti);
  // TOUJOURS descendre : le raccourci #donjon laisse le joueur DEHORS.
  // Sans ce pas, la sonde mesure le village en croyant mesurer le donjon
  // (erreur du 22/08 : elle a rendu « 298 cases » qui étaient celles du village).
  await lire('window.D.allerA(' + ETAGE + ')'); await dodo(5000);
  await dodo(2500);
  console.log('étage :', await lire('String(window.D.etageCourant)'));
  console.log('dehors ?', await lire('!!(window.D.grid && window.D.grid.length===56)'));

  const brut = await lire(`(function(){
    var g = window.D.grid, T = window.D.T, W = window.D.W, H = g.length;
    var MUR = 0;
    // où est le joueur, en cases
    var jx = Math.floor(window.D.joueur.x / T), jy = Math.floor(window.D.joueur.z / T);
    // l'eau coule depuis le joueur, case par case, sans traverser les murs
    var vu = [], f = [[jx,jy]], n = 0;
    for (var y=0;y<H;y++){ vu.push(new Array(W).fill(false)); }
    if (g[jy] && g[jy][jx] !== MUR){ vu[jy][jx] = true; n = 1; } else { f = []; }
    while (f.length){
      var c = f.pop(), x = c[0], y = c[1];
      var v = [[x+1,y],[x-1,y],[x,y+1],[x,y-1]];
      for (var i=0;i<4;i++){
        var a = v[i][0], b = v[i][1];
        if (a<0||b<0||a>=W||b>=H) continue;
        if (vu[b][a]) continue;
        if (g[b][a] === MUR) continue;
        vu[b][a] = true; n++; f.push([a,b]);
      }
    }
    // combien de cases praticables en tout ?
    var total = 0, ilots = 0;
    for (var y2=0;y2<H;y2++) for (var x2=0;x2<W;x2++) if (g[y2][x2] !== MUR){ total++; if(!vu[y2][x2]) ilots++; }
    // la sortie
    var d = window.D.doorPos;
    // où sont les cercles de téléportation, et peut-on les atteindre ?
    var sortieOk = d ? !!(vu[d.y] && vu[d.y][d.x]) : null;
    // les salles : combien sont atteignables ?
    var salles = (window.D.rooms||[]).map(function(r){
      var cx = Math.floor(r.x + r.w/2), cy = Math.floor(r.y + r.h/2);
      return { x:cx, y:cy, atteignable: !!(vu[cy] && vu[cy][cx]) };
    });
    return JSON.stringify({
      joueur:[jx,jy], casesAtteintes:n, casesPraticables:total, casesCoupees:ilots,
      sortie: d ? [d.x,d.y] : null, sortieAtteignable: sortieOk,
      salles: salles, sallesCoupees: salles.filter(function(s){return !s.atteignable;}).length
    });
  })()`);
  console.log(brut);
  ws.close(); process.exit(0);
})();
