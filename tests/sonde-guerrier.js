// SONDE GUERRIER — l'adversaire bouge-t-il TOUT le corps, ou juste les bras ?
const http=require('http'),dodo=ms=>new Promise(r=>setTimeout(r,ms));
const P=process.argv[2]||9299;
const gj=p=>new Promise((r,j)=>http.get('http://127.0.0.1:'+P+p,x=>{let d='';x.on('data',c=>d+=c);x.on('end',()=>{try{r(JSON.parse(d))}catch(e){j(e)}})}).on('error',j));
(async()=>{const pg=(await gj('/json')).find(x=>x.type==='page'&&x.webSocketDebuggerUrl);
const ws=new WebSocket(pg.webSocketDebuggerUrl);let id=0;const a={};
const env=(m,p)=>new Promise(r=>{const i=++id;a[i]=r;ws.send(JSON.stringify({id:i,method:m,params:p||{}}))});
ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&a[m.id]){a[m.id](m.result||{});delete a[m.id]}};
await new Promise(r=>ws.onopen=r);await env('Runtime.enable');await env('Page.enable');
const L=async x=>{const r=await env('Runtime.evaluate',{expression:x,returnByValue:true});return r.result&&r.result.value};
await env('Page.navigate',{url:'http://127.0.0.1:8099/index.html?t='+Date.now()+'#arene'});
for(let i=0;i<30;i++){await L('(function(){var b=document.getElementById("jouer");if(b&&!b.disabled)b.click()})()');await dodo(1000);if((await L('window.D&&window.D.etat'))==='jeu')break;}
await dodo(4000);
console.log('guerrier present:',await L('!!window.D.guerrier'));
console.log('vrmClips (vraies anims recopiees):',await L('window.D.guerrier?window.D.guerrier.vrmClips:"?"'));
// mesurer bras vs jambe sur 6 secondes
const lire=k=>L(`(function(){var g=window.D.guerrier;if(!g||!g.vrm)return null;var b=g.vrm.humanoid.getRawBoneNode(${JSON.stringify(k)});return b?(b.rotation.x+b.rotation.z):null;})()`);
let bras={min:9,max:-9}, jambe={min:9,max:-9}, hanche={min:9,max:-9};
for(let i=0;i<20;i++){
  const rb=await lire('rightUpperArm'), rj=await lire('rightUpperLeg'), rh=await lire('hips');
  if(rb!=null){bras.min=Math.min(bras.min,rb);bras.max=Math.max(bras.max,rb);}
  if(rj!=null){jambe.min=Math.min(jambe.min,rj);jambe.max=Math.max(jambe.max,rj);}
  if(rh!=null){hanche.min=Math.min(hanche.min,rh);hanche.max=Math.max(hanche.max,rh);}
  await dodo(300);
}
console.log('amplitude BRAS :',(bras.max-bras.min).toFixed(3));
console.log('amplitude JAMBE:',(jambe.max-jambe.min).toFixed(3));
console.log('amplitude HANCHE:',(hanche.max-hanche.min).toFixed(3));
ws.close();process.exit(0);})();
