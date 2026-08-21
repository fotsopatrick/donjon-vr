const http=require('http'),dodo=ms=>new Promise(r=>setTimeout(r,ms));
const PORT=process.argv[2]||9265;
const gj=p=>new Promise((r,j)=>http.get('http://127.0.0.1:'+PORT+p,x=>{let d='';x.on('data',c=>d+=c);x.on('end',()=>{try{r(JSON.parse(d))}catch(e){j(e)}})}).on('error',j));
(async()=>{
  const pg=(await gj('/json')).find(x=>x.type==='page'&&x.webSocketDebuggerUrl);
  const ws=new WebSocket(pg.webSocketDebuggerUrl);let id=0;const a={};
  const env=(m,p)=>new Promise(r=>{const i=++id;a[i]=r;ws.send(JSON.stringify({id:i,method:m,params:p||{}}))});
  ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&a[m.id]){a[m.id](m.result||{});delete a[m.id]}};
  await new Promise(r=>ws.onopen=r);await env('Runtime.enable');await env('Page.enable');
  const L=async x=>{const r=await env('Runtime.evaluate',{expression:x,returnByValue:true});return r.result&&r.result.value};
  await env('Page.navigate',{url:'http://127.0.0.1:8099/index.html?t='+Date.now()+'#village'});
  for(let i=0;i<30;i++){await L('(function(){var b=document.getElementById("jouer");if(b&&!b.disabled)b.click()})()');await dodo(1000);if((await L('window.D&&window.D.etat'))==='jeu')break;}
  console.log('etat jeu:',await L('window.D&&window.D.etat'));
  await L('window.D.allerA(0)');await dodo(4000);
  console.log('murIM existe ?', await L('!!(window.D && window.D.murIM)'));
  console.log('mesure:', await L(`(function(){var m=window.D.murIM;if(!m)return "murIM null";var h=m.geometry.parameters?m.geometry.parameters.height:"pas de parameters";var mat=new window.D.THREE.Matrix4(),p=new window.D.THREE.Vector3();m.getMatrixAt(0,mat);p.setFromMatrixPosition(mat);return JSON.stringify({count:m.count,hauteurBoite:h,posY_premier:Math.round(p.y*100)/100,bas:Math.round((p.y-(h/2))*100)/100});})()`));
  ws.close();process.exit(0);
})();
