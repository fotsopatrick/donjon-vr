// capturer.js — prend une capture d'un écran du jeu (Chrome headless via CDP).
//   node capturer.js "http://localhost:8091/#arene" sortie.png
const { spawn } = require('child_process');
const fs = require('fs');
const URL = process.argv[2], OUT = process.argv[3];
const chrome = spawn('google-chrome', ['--headless=new','--no-sandbox','--use-gl=angle',
  '--use-angle=swiftshader','--enable-webgl','--window-size=1280,800',
  '--remote-debugging-port=9337','about:blank'], {stdio:'ignore'});
const sleep = ms => new Promise(r=>setTimeout(r,ms));
(async()=>{
  await sleep(1500);
  const list = await (await fetch('http://localhost:9337/json')).json();
  const page = list.find(t=>t.type==='page');
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id=0; const pend={};
  const send=(m,p={})=>{ const i=++id; ws.send(JSON.stringify({id:i,method:m,params:p})); return new Promise(r=>pend[i]=r); };
  await new Promise(r=>ws.onopen=r);
  ws.onmessage=e=>{ const d=JSON.parse(e.data); if(d.id&&pend[d.id]){pend[d.id](d.result);delete pend[d.id];} };
  await send('Page.enable'); await send('Page.navigate',{url:URL});
  await sleep(7000);
  const shot = await send('Page.captureScreenshot',{format:'png'});
  fs.writeFileSync(OUT, Buffer.from(shot.data,'base64'));
  ws.close(); chrome.kill(); process.exit(0);
})().catch(e=>{console.error(e);chrome.kill();process.exit(1);});
