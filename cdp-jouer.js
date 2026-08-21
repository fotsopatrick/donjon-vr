// Harnais de pilotage du jeu via Chrome DevTools Protocol.
// Usage: node cdp-jouer.js '[{"nav":"#village"},{"wait":4000},{"eval":"..."},{"key":"KeyW","ms":800},{"shot":"/tmp/x.png"}]'
const http=require('http'), fs=require('fs');
const actions=JSON.parse(process.argv[2]||'[]');
function getJSON(p){return new Promise((res,rej)=>{http.get('http://127.0.0.1:9222'+p,r=>{let d='';r.on('data',c=>d+=c);r.on('end',()=>{try{res(JSON.parse(d))}catch(e){rej(e)}});}).on('error',rej);});}
const VK={KeyW:87,KeyA:65,KeyS:83,KeyD:68,KeyZ:90,KeyQ:81,KeyE:69,KeyR:82,KeyF:70,KeyX:88,KeyV:86,KeyG:71,Space:32,ShiftLeft:16,ArrowLeft:37,ArrowRight:39,ArrowUp:38,ArrowDown:40};
(async()=>{
  const t=await getJSON('/json'); const page=t.find(x=>x.type==='page'&&x.webSocketDebuggerUrl);
  const ws=new WebSocket(page.webSocketDebuggerUrl); let id=0; const pend={};
  const send=(m,p)=>new Promise(r=>{const i=++id;pend[i]=r;ws.send(JSON.stringify({id:i,method:m,params:p||{}}));});
  ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.id&&pend[m.id]){pend[m.id](m.result||{});delete pend[m.id];}};
  await new Promise(r=>ws.onopen=r);
  await send('Runtime.enable'); await send('Page.enable');
  const keyEv=async(code,type)=>{ const key=code.replace('Key','').toLowerCase(); await send('Input.dispatchKeyEvent',{type,code,key,windowsVirtualKeyCode:VK[code]||0,nativeVirtualKeyCode:VK[code]||0}); };
  for(const a of actions){
    if(a.nav){ await send('Page.navigate',{url:'about:blank'}); await new Promise(r=>setTimeout(r,250)); await send('Page.navigate',{url:'http://127.0.0.1:8099/index.html'+a.nav}); }
    if(a.wait){ await new Promise(r=>setTimeout(r,a.wait)); }
    if(a.click){ await send('Input.dispatchMouseEvent',{type:'mousePressed',x:a.click[0],y:a.click[1],button:'left',clickCount:1}); await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:a.click[0],y:a.click[1],button:'left',clickCount:1}); }
    if(a.key){ await keyEv(a.key,'keyDown'); await new Promise(r=>setTimeout(r,a.ms||300)); await keyEv(a.key,'keyUp'); }
    if(a.kd){ await keyEv(a.kd,'keyDown'); }
    if(a.ku){ await keyEv(a.ku,'keyUp'); }
    if(a.eval){ const {result}=await send('Runtime.evaluate',{expression:a.eval,returnByValue:true}); console.log('EVAL:', JSON.stringify(result&&result.value)); }
    if(a.shot){ const {data}=await send('Page.captureScreenshot',{format:'png'}); fs.writeFileSync(a.shot,Buffer.from(data,'base64')); console.log('SHOT:',a.shot); }
  }
  ws.close(); process.exit(0);
})();
