// cdp-demo-alice.js — preuve « l'avatar bouge » piloté par Alice.
// Ouvre  index.html?mission=1#village  (Alice prend les commandes),
// capture des frames au moment du mouvement, mesure D.pos avant/après.
// Usage : node cdp-demo-alice.js <port> [..sorties]
const http=require('http'), fs=require('fs');
const PORT=process.argv[2]||9249;
const OUTS=process.argv.slice(3);
const wait=(ms)=>new Promise(r=>setTimeout(r,ms));
function getJSON(p){return new Promise((res,rej)=>{http.get('http://127.0.0.1:'+PORT+p,r=>{let d='';r.on('data',c=>d+=c);r.on('end',()=>{try{res(JSON.parse(d))}catch(e){rej(e)}});}).on('error',rej);});}
(async()=>{
  console.log('port',PORT,'sorties',String(OUTS));
  let t; for(let i=0;i<25;i++){ try{ t=await getJSON('/json'); if(t.some(x=>x.type==='page'&&x.webSocketDebuggerUrl))break; }catch(e){console.log('wait',e.message);} await wait(400); }
  const page=t.find(x=>x.type==='page'&&x.webSocketDebuggerUrl);
  if(!page){ console.log('❌ PAS DE PAGE CDP'); process.exit(1); }
  const ws=new WebSocket(page.webSocketDebuggerUrl); let id=0; const pend={};
  const send=(m,p)=>new Promise((res,rej)=>{const i=++id;const to=setTimeout(()=>{delete pend[i];rej(new Error('timeout '+m));},15000);pend[i]=(r)=>{clearTimeout(to);res(r);};ws.send(JSON.stringify({id:i,method:m,params:p||{}}));});
  ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.id&&pend[m.id]){pend[m.id](m.result||{});delete pend[m.id];}};
  ws.onerror=()=>{console.log('WS ERROR');};
  await new Promise(r=>ws.onopen=r);
  try{
    await send('Runtime.enable'); await send('Page.enable');
    await send('Page.navigate',{url:'http://127.0.0.1:8099/index.html?mission=1#village'});
    console.log('navigation ok — chargement du hameau…');
    await wait(6500);
    const evalv=async(label)=>{ const r=await send('Runtime.evaluate',{expression:'D && D.pos ? D.pos : {x:-1}',returnByValue:true}); const v=r.result&&r.result.value||{}; console.log('POS',label,JSON.stringify(v)); return v; };
    const p0=await evalv('avant');
    let i=0;
    for(const f of OUTS){
      await wait(950);
      try{ const {data}=await send('Page.captureScreenshot',{format:'png'}); fs.writeFileSync(f,Buffer.from(data,'base64')); console.log('SHOT',f,fs.statSync(f).size); }catch(e){ console.log('shot échoué',e.message); }
      i++;
    }
    await wait(400);
    const p1=await evalv('après');
    if(p0&&p0.x!==undefined&&p1.x!==undefined){
      const dx=p1.x-p0.x, dz=p1.z-p0.z;
      console.log('BOUGÉE ? delta(%.2f, %.2f) — %s', dx,dz, (Math.abs(dx)>0.01||Math.abs(dz)>0.01)?'OUI ✅':'NON ❌');
    }
  }catch(e){ console.log('err',e.message); }
  ws.close(); process.exit(0);
})();