// TEST DE COMPORTEMENT DU MENU (via CDP) — clique chaque bouton, vérifie l'effet réel.
const http=require('http');
function getJSON(p){return new Promise((res,rej)=>{http.get('http://127.0.0.1:9222'+p,r=>{let d='';r.on('data',c=>d+=c);r.on('end',()=>{try{res(JSON.parse(d))}catch(e){rej(e)}});}).on('error',rej);});}
(async()=>{
  const t=await getJSON('/json'); const page=t.find(x=>x.type==='page'&&x.webSocketDebuggerUrl);
  const ws=new WebSocket(page.webSocketDebuggerUrl); let id=0; const pend={};
  const send=(m,p)=>new Promise(r=>{const i=++id;pend[i]=r;ws.send(JSON.stringify({id:i,method:m,params:p||{}}));});
  ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.id&&pend[m.id]){pend[m.id](m.result||{});delete pend[m.id];}};
  await new Promise(r=>ws.onopen=r); await send('Runtime.enable'); await send('Page.enable');
  const ev=async(x)=>{const {result}=await send('Runtime.evaluate',{expression:x,returnByValue:true});return result&&result.value;};
  const clicSel=async(sel)=>{ await ev(`(function(){var b=document.querySelector('${sel}');var r=b.getBoundingClientRect();window.__cx=r.x+r.width/2;window.__cy=r.y+r.height/2;})()`);
    const x=await ev('window.__cx'), y=await ev('window.__cy');
    await send('Input.dispatchMouseEvent',{type:'mousePressed',x,y,button:'left',clickCount:1});
    await send('Input.dispatchMouseEvent',{type:'mouseReleased',x,y,button:'left',clickCount:1}); };
  const reload=async()=>{ await send('Page.navigate',{url:'about:blank'}); await new Promise(r=>setTimeout(r,300));
    await send('Page.navigate',{url:'http://127.0.0.1:8099/index.html#'}); await new Promise(r=>setTimeout(r,10000)); };
  let ok=0,ko=0; const check=(n,c)=>{ if(c){ok++;console.log('  ✓ '+n);} else {ko++;console.log('  ✗ '+n);} };
  // 1. cliquer "Donjon" puis "Entrer" -> on doit être au donjon (etage numérique)
  await reload(); await clicSel('.entree-tab[data-niv="1"]');
  const nivApresDonjon = await ev('(function(){var el=document.querySelector(".entree-tab[data-niv=\\"1\\"]");return el.classList.contains("on");})()');
  check('clic Donjon -> onglet Donjon actif', nivApresDonjon===true);
  await clicSel('#jouer'); await new Promise(r=>setTimeout(r,9000));
  const etDonjon = await ev('document.getElementById("etage").textContent');
  check('Donjon -> etage numerique (pas —)', etDonjon && !etDonjon.includes('—') && !etDonjon.includes('Entra'));
  console.log('    etage obtenu:', JSON.stringify(etDonjon));
  // 2. cliquer "Village" -> onglet Village actif
  await reload(); await clicSel('.entree-tab[data-niv="0"]');
  const vilActif = await ev('document.querySelector(".entree-tab[data-niv=\\"0\\"]").classList.contains("on")');
  check('clic Village -> onglet Village actif', vilActif===true);
  await clicSel('#jouer'); await new Promise(r=>setTimeout(r,9000));
  const etVil = await ev('document.getElementById("etage").textContent');
  check('Village -> etage = —', etVil && etVil.includes('—'));
  console.log('    etage obtenu:', JSON.stringify(etVil));
  console.log(`\n  ${ok} reussis, ${ko} echoues`);
  process.exit(0);
})();
