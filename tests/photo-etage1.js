const http=require('http'),fs=require('fs');
const PORT=process.argv[2]||9264, dodo=ms=>new Promise(r=>setTimeout(r,ms));
const gj=p=>new Promise((r,j)=>http.get('http://127.0.0.1:'+PORT+p,x=>{let d='';x.on('data',c=>d+=c);x.on('end',()=>{try{r(JSON.parse(d))}catch(e){j(e)}})}).on('error',j));
(async()=>{
  const pg=(await gj('/json')).find(x=>x.type==='page'&&x.webSocketDebuggerUrl);
  const ws=new WebSocket(pg.webSocketDebuggerUrl);let id=0;const a={};
  const env=(m,p)=>new Promise(r=>{const i=++id;a[i]=r;ws.send(JSON.stringify({id:i,method:m,params:p||{}}))});
  ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&a[m.id]){a[m.id](m.result||{});delete a[m.id]}};
  await new Promise(r=>ws.onopen=r); await env('Runtime.enable'); await env('Page.enable');
  const L=async x=>{const r=await env('Runtime.evaluate',{expression:x,returnByValue:true});return r.result&&r.result.value};
  await env('Page.navigate',{url:'http://127.0.0.1:8099/index.html?t='+Date.now()+'#donjon'});
  for(let i=0;i<30;i++){await L('(function(){var b=document.getElementById("jouer");if(b&&!b.disabled)b.click()})()');await dodo(1000);if((await L('window.D&&window.D.etat'))==='jeu')break;}
  await L('window.D.allerA(1)'); await dodo(5000);
  // se placer au départ, regarder vers le cercle, vue de dos
  await L('(function(){var d=window.D.doorPos;window.D.joueur.vol=false;})()');
  for(let i=0;i<4 && !(await L('window.D.avatar.visible'));i++){await L('window.D.basculerVue()');await dodo(300);}
  await dodo(1500);
  const info=await L('JSON.stringify({etage:String(window.D.etageCourant),joueur:[Math.round(window.D.joueur.x),Math.round(window.D.joueur.z)]})');
  console.log('etat:',info);
  const {data}=await env('Page.captureScreenshot',{format:'png'});
  fs.mkdirSync(__dirname+'/captures',{recursive:true});
  fs.writeFileSync(__dirname+'/captures/etage1_arrivee.png',Buffer.from(data,'base64'));
  console.log('PHOTO: tests/captures/etage1_arrivee.png');
  ws.close();process.exit(0);
})();
