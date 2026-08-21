const http=require('http'), fs=require('fs');
const hash=process.argv[2]||'village', outf=process.argv[3]||'/tmp/shot.png';
function getJSON(p){return new Promise((res,rej)=>{http.get('http://127.0.0.1:9222'+p,r=>{let d='';r.on('data',c=>d+=c);r.on('end',()=>{try{res(JSON.parse(d))}catch(e){rej(e)}});}).on('error',rej);});}
(async()=>{
  const t=await getJSON('/json'); const page=t.find(x=>x.type==='page'&&x.webSocketDebuggerUrl);
  const ws=new WebSocket(page.webSocketDebuggerUrl); let id=0; const pend={};
  const send=(m,p)=>new Promise(r=>{const i=++id;pend[i]=r;ws.send(JSON.stringify({id:i,method:m,params:p||{}}));});
  ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.id&&pend[m.id]){pend[m.id](m.result);delete pend[m.id];}};
  await new Promise(r=>ws.onopen=r);
  await send('Page.enable');
  await send('Page.navigate',{url:'http://127.0.0.1:8099/index.html#'+hash});
  await new Promise(r=>setTimeout(r,7000));
  const {data}=await send('Page.captureScreenshot',{format:'png'});
  fs.writeFileSync(outf, Buffer.from(data,'base64'));
  console.log('SHOT:',outf,fs.statSync(outf).size);
  ws.close(); process.exit(0);
})();
