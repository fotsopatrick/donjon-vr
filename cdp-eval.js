const http=require('http');
function getJSON(p){return new Promise((res,rej)=>{http.get('http://127.0.0.1:9222'+p,r=>{let d='';r.on('data',c=>d+=c);r.on('end',()=>{try{res(JSON.parse(d))}catch(e){rej(e)}});}).on('error',rej);});}
(async()=>{
  const t=await getJSON('/json'); const page=t.find(x=>x.type==='page'&&x.webSocketDebuggerUrl);
  const ws=new WebSocket(page.webSocketDebuggerUrl); let id=0; const pend={};
  const send=(m,p)=>new Promise(r=>{const i=++id;pend[i]=r;ws.send(JSON.stringify({id:i,method:m,params:p||{}}));});
  ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.id&&pend[m.id]){pend[m.id](m.result);delete pend[m.id];}};
  await new Promise(r=>ws.onopen=r);
  await send('Runtime.enable');
  await send('Page.navigate',{url:'http://127.0.0.1:8099/index.html#village'});
  await new Promise(r=>setTimeout(r,6000));
  const expr = `JSON.stringify({hash:location.hash, D:(window.D?Object.keys(window.D):null), Dniveau:(window.D&&window.D.niveau), Ddepart:(window.D&&window.D.departNiveau)})`;
  const {result}=await send('Runtime.evaluate',{expression:expr,returnByValue:true});
  console.log('ETAT:', result.value);
  ws.close(); process.exit(0);
})();
