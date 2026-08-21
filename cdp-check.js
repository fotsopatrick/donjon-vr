const http = require('http');
function getJSON(p){ return new Promise((res,rej)=>{ http.get('http://127.0.0.1:9222'+p, r=>{ let d=''; r.on('data',c=>d+=c); r.on('end',()=>{ try{res(JSON.parse(d))}catch(e){rej(e)} }); }).on('error',rej); }); }
(async()=>{
  let targets; for(let i=0;i<20;i++){ try{ targets=await getJSON('/json'); if(targets.length)break; }catch(e){} await new Promise(r=>setTimeout(r,300)); }
  const page = (targets||[]).find(t=>t.type==='page' && t.webSocketDebuggerUrl);
  if(!page){ console.log('PAS DE PAGE'); process.exit(0); }
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id=0; const send=(m,p)=>ws.send(JSON.stringify({id:++id,method:m,params:p||{}}));
  const out=[];
  ws.onmessage=(e)=>{ const m=JSON.parse(e.data);
    if(m.method==='Runtime.exceptionThrown'){ const x=m.params.exceptionDetails; out.push('❌ EXCEPTION: '+(x.exception&&x.exception.description||x.text)); }
    if(m.method==='Runtime.consoleAPICalled' && ['error','warning'].includes(m.params.type)){ out.push('⚠️ '+m.params.type+': '+m.params.args.map(a=>a.value||a.description||'').join(' ')); }
  };
  ws.onopen=async()=>{
    send('Runtime.enable'); send('Log.enable'); send('Page.enable');
    await new Promise(r=>setTimeout(r,400));
    send('Page.navigate',{url:'http://127.0.0.1:8099/index.html#village'});
    await new Promise(r=>setTimeout(r,7000));
    console.log('=== CONSOLE (village) ==='); console.log(out.length?out.join('\n'):'(aucune erreur)');
    ws.close(); process.exit(0);
  };
})();
