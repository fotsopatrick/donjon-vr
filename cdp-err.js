const http=require('http');
function getJSON(p){return new Promise((res,rej)=>{http.get('http://127.0.0.1:9222'+p,r=>{let d='';r.on('data',c=>d+=c);r.on('end',()=>{try{res(JSON.parse(d))}catch(e){rej(e)}});}).on('error',rej);});}
(async()=>{
  const t=await getJSON('/json'); const page=t.find(x=>x.type==='page'&&x.webSocketDebuggerUrl);
  const ws=new WebSocket(page.webSocketDebuggerUrl); let id=0;
  const send=(m,p)=>ws.send(JSON.stringify({id:++id,method:m,params:p||{}}));
  const out=[];
  ws.onmessage=e=>{const m=JSON.parse(e.data);
    if(m.method==='Runtime.exceptionThrown'){const x=m.params.exceptionDetails;out.push('EXC: '+(x.exception&&x.exception.description||x.text));}
    if(m.method==='Runtime.consoleAPICalled'&&m.params.type==='error'){out.push('ERR: '+m.params.args.map(a=>a.value||a.description||'').join(' '));}
  };
  ws.onopen=async()=>{ send('Runtime.enable');
    await new Promise(r=>setTimeout(r,300));
    send('Page.navigate',{url:'http://127.0.0.1:8099/index.html#donjon'});
    await new Promise(r=>setTimeout(r,9000));
    const uniq=[...new Set(out)];
    console.log(uniq.length?uniq.slice(0,6).join('\n'):'(aucune exception)');
    process.exit(0);
  };
})();
