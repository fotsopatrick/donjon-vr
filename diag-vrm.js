// Diagnostic VRM : charge le jeu, capture les erreurs console, vérifie le chargement du VRM.
const http=require('http'), fs=require('fs');
const PORT=process.argv[2]||9250, OUT=process.argv[3]||'/tmp/vrm-diag.png';
const getJSON=p=>new Promise((res,rej)=>{http.get('http://127.0.0.1:'+PORT+p,r=>{let d='';r.on('data',c=>d+=c);r.on('end',()=>{try{res(JSON.parse(d))}catch(e){rej(e)}})}).on('error',rej)});
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  const t=await getJSON('/json'); const page=t.find(x=>x.type==='page'&&x.webSocketDebuggerUrl);
  const ws=new WebSocket(page.webSocketDebuggerUrl); let id=0; const pend={}; const errs=[];
  const send=(m,p)=>new Promise(r=>{const i=++id;pend[i]=r;ws.send(JSON.stringify({id:i,method:m,params:p||{}}))});
  ws.onmessage=e=>{const m=JSON.parse(e.data);
    if(m.id&&pend[m.id]){pend[m.id](m.result||{});delete pend[m.id];}
    if(m.method==='Runtime.exceptionThrown'){errs.push('EXCEPTION: '+(m.params.exceptionDetails.exception?.description||m.params.exceptionDetails.text));}
    if(m.method==='Runtime.consoleAPICalled'&&['error','warning'].includes(m.params.type)){errs.push(m.params.type.toUpperCase()+': '+m.params.args.map(a=>a.value||a.description||'').join(' '));}
  };
  await new Promise(r=>ws.onopen=r);
  await send('Runtime.enable'); await send('Page.enable');
  await send('Page.navigate',{url:'about:blank'}); await sleep(200);
  await send('Page.navigate',{url:'http://127.0.0.1:8099/index.html?t='+process.argv[4]+'#arene'});
  await sleep(12000);   // laisse le script s'exécuter
  const ev=async x=>{const{result}=await send('Runtime.evaluate',{expression:x,returnByValue:true});return result&&result.value;};
  // ATTENTE ACTIVE : on clique dès que le bouton est prêt, puis on attend l'état "jeu" (robuste sous charge)
  let started=false;
  for(let i=0;i<40 && !started;i++){
    await ev('(function(){var b=document.getElementById("jouer");if(b&&!b.disabled&&window.D&&window.D.etat!=="jeu")b.click();})()');
    await sleep(1500);
    started = (await ev('window.D&&window.D.etat')) === 'jeu';
  }
  console.log('persoCustom estVRM:', await ev('!!(window.D&&window.D.MODELES&&window.D.MODELES.persoCustom&&window.D.MODELES.persoCustom.userData&&window.D.MODELES.persoCustom.userData.estVRM)'));
  console.log('etat après clic:', await ev('window.D&&window.D.etat'));
  await ev('window.D&&window.D.etat==="jeu"&&window.D.basculerVue&&window.D.basculerVue()');
  await new Promise(r=>setTimeout(r,500));
  const key=async(ty)=>send('Input.dispatchKeyEvent',{type:ty,code:'KeyW',key:'w',windowsVirtualKeyCode:87,nativeVirtualKeyCode:87});
  await key('keyDown'); await new Promise(r=>setTimeout(r,650));
  let s1=await send('Page.captureScreenshot',{format:'png'}); fs.writeFileSync(OUT,Buffer.from(s1.data,'base64')); console.log('SHOT:',OUT);
  await new Promise(r=>setTimeout(r,380));
  let s2=await send('Page.captureScreenshot',{format:'png'}); fs.writeFileSync(OUT.replace('.png','-b.png'),Buffer.from(s2.data,'base64')); console.log('SHOT:',OUT.replace('.png','-b.png'));
  await key('keyUp');
  ws.close(); process.exit(0);
})();
