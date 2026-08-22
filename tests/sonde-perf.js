// SONDE PERF — compte les appels de dessin d'un lieu, rangés par cause.
// Le goulot du jeu, ce sont les APPELS de dessin (pas les triangles).
const http=require('http'),dodo=ms=>new Promise(r=>setTimeout(r,ms));
const P=process.argv[2]||9272, LIEU=process.argv[3]||'#village';
const gj=p=>new Promise((r,j)=>http.get('http://127.0.0.1:'+P+p,x=>{let d='';x.on('data',c=>d+=c);x.on('end',()=>{try{r(JSON.parse(d))}catch(e){j(e)}})}).on('error',j));
(async()=>{const pg=(await gj('/json')).find(x=>x.type==='page'&&x.webSocketDebuggerUrl);
const ws=new WebSocket(pg.webSocketDebuggerUrl);let id=0;const a={};
const env=(m,p)=>new Promise(r=>{const i=++id;a[i]=r;ws.send(JSON.stringify({id:i,method:m,params:p||{}}))});
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&a[m.id]){a[m.id](m.result||{});delete a[m.id]}};
await new Promise(r=>ws.onopen=r);await env('Runtime.enable');await env('Page.enable');
const L=async x=>{const r=await env('Runtime.evaluate',{expression:x,returnByValue:true});return r.result&&r.result.value};
await env('Page.navigate',{url:'http://127.0.0.1:8099/index.html?t='+Date.now()+LIEU});
for(let i=0;i<30;i++){await L('(function(){var b=document.getElementById("jouer");if(b&&!b.disabled)b.click()})()');await dodo(1000);if((await L('window.D&&window.D.etat'))==='jeu')break;}
await dodo(6000);
console.log(await L(`(function(){
  var S=window.D.scene, vis=0, tot=0, tri=0, parGeo={}, sansPartage=0;
  S.traverse(function(o){ if(!o.isMesh && !o.isInstancedMesh) return; tot++;
    if(!o.visible) return; vis++;
    if(o.isInstancedMesh){ parGeo['(instancié '+o.count+')']=(parGeo['(instancié '+o.count+')']||0)+1; return; }
    var g=o.geometry&&o.geometry.type||'?';
    parGeo[g]=(parGeo[g]||0)+1;
    if(o.geometry&&o.geometry.index){tri+=o.geometry.index.count/3;}
  });
  var top=Object.entries(parGeo).sort(function(x,y){return y[1]-x[1]}).slice(0,12);
  return JSON.stringify({meshes_visibles:vis, meshes_total:tot, triangles_k:Math.round(tri/1000), par_type:top}, null, 1);
})()`));
ws.close();process.exit(0);})();
