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
  await dodo(4000);
  console.log(await ev(`(function(){
    function moyenne(m){
      try{
        var img=m.map.image; if(!img||!img.width) return null;
        var c=document.createElement('canvas'); var w=Math.min(16,img.width),h=Math.min(16,img.height);
        c.width=w;c.height=h; var g=c.getContext('2d'); g.drawImage(img,0,0,w,h);
        var d=g.getImageData(0,0,w,h).data; var sr=0,sg=0,sb=0,n=0;
        for(var i=0;i<d.length;i+=4){sr+=d[i];sg+=d[i+1];sb+=d[i+2];n++;}
        return {r:Math.round(sr/n),g:Math.round(sg/n),b:Math.round(sb/n),image:img.constructor.name};
      }catch(e){return {err:String(e)}}
    }
    var trouves=[]; var vus=new Set();
    window.D.scene.traverse(function(o){
      if(!o.isMesh||!o.material) return;
      var m=Array.isArray(o.material)?o.material[0]:o.material;
      if(!m||!m.map||vus.has(m)) return; vus.add(m);
      var mo=moyenne(m);
      if(mo&&!mo.err&&(mo.r-mo.g)>40&&(mo.r-mo.b)>60){ trouves.push({c:m.color.getHexString(),moy:mo}); }
    });
    return JSON.stringify(trouves.slice(0,12));
  })()`));
  ws.close(); process.exit(0);
})().catch(e => { console.log('ERR', e.message); process.exit(1); });
