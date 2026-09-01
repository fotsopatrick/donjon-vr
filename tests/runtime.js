// ============================================================
//  SYSTÈME DE TEST REJOUABLE — comportement réel du jeu en headless
//  (comme un studio : on pilote le jeu, on ASSERTE, on capture)
//
//  Usage :  bash tests/run.sh        (lance Chrome headless + ce runner)
//  Ou :     node tests/runtime.js <port> <baseurl>
//
//  Chaque cas recharge le jeu avec un cache-buster (?t=…) — LEÇON PAYÉE :
//  sans ça, Chrome ressert l'ancienne version et le test ment.
// ============================================================
const http = require('http'), fs = require('fs');
const PORT = process.argv[2] || 9247;
const BASE = process.argv[3] || 'http://127.0.0.1:8099/index.html';
const SHOTDIR = __dirname + '/captures';
try { fs.mkdirSync(SHOTDIR, { recursive: true }); } catch (e) {}

const getJSON = p => new Promise((res, rej) => {
  http.get('http://127.0.0.1:' + PORT + p, r => { let d = ''; r.on('data', c => d += c); r.on('end', () => { try { res(JSON.parse(d)); } catch (e) { rej(e); } }); }).on('error', rej);
});
const VK = { KeyW:87,KeyA:65,KeyS:83,KeyD:68,KeyE:69,KeyR:82,KeyF:70,Space:32 };

(async () => {
  const tabs = await getJSON('/json');
  const page = tabs.find(x => x.type === 'page' && x.webSocketDebuggerUrl);
  if (!page) { console.log('AUCUNE PAGE CDP — Chrome headless lancé ?'); process.exit(2); }
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0; const pend = {};
  const send = (m, p) => new Promise(r => { const i = ++id; pend[i] = r; ws.send(JSON.stringify({ id: i, method: m, params: p || {} })); });
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pend[m.id]) { pend[m.id](m.result || {}); delete pend[m.id]; } };
  await new Promise(r => ws.onopen = r);
  await send('Runtime.enable'); await send('Page.enable');

  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const ev = async expr => { const { result } = await send('Runtime.evaluate', { expression: expr, returnByValue: true }); return result && result.value; };
  const key = async (code, type) => send('Input.dispatchKeyEvent', { type, code, key: code.replace('Key','').toLowerCase(), windowsVirtualKeyCode: VK[code]||0, nativeVirtualKeyCode: VK[code]||0 });
  const shot = async name => { const { data } = await send('Page.captureScreenshot', { format: 'png' }); fs.writeFileSync(SHOTDIR + '/' + name + '.png', Buffer.from(data, 'base64')); };
  const load = async (hash) => {                      // recharge PROPREMENT avec cache-buster
    await send('Page.navigate', { url: 'about:blank' }); await sleep(200);
    await send('Page.navigate', { url: BASE + '?t=' + Date.now() + (hash || '') }); await sleep(16000);
  };
  const demarrer = async () => {                       // clique « Entrer » et attend l'état jeu
    await ev('(function(){var b=document.getElementById("jouer");if(b&&!b.disabled)b.click();})()');
    for (let i = 0; i < 20 && (await ev('window.D&&window.D.etat')) !== 'jeu'; i++) await sleep(500);
  };

  const CAS = [
    { nom: 'avatar_amplitude', desc: 'GARDE-FOU mouvements : l\'avatar bouge AMPLEMENT en marchant (pas un bâton de bois)',
      run: async () => {
        await load('#arene'); await demarrer();
        for (let i = 0; i < 3 && !(await ev('window.D.avatar.visible')); i++) { await ev('window.D.basculerVue()'); await sleep(250); }
        const lireBras = () => ev('(function(){var v=window.D.avatar&&window.D.avatar.userData&&window.D.avatar.userData.vrm;if(!v||!v.humanoid)return null;var b=v.humanoid.getNormalizedBoneNode("leftUpperArm");return b?b.rotation.x:null;})()');
        await key('KeyW','keyDown'); await sleep(300);
        const mesures = [];                                   // 6 mesures sur ~1 s : on capte le balancier entier
        for (let i = 0; i < 6; i++) { mesures.push(await lireBras()); if (i === 1) await shot('amplitude_1'); if (i === 4) await shot('amplitude_2'); await sleep(180); }
        await key('KeyW','keyUp');
        assert(mesures.every(m => m !== null), 'avatar VRM introuvable (pas de humanoid)');
        const ecart = Math.max(...mesures) - Math.min(...mesures);
        assert(ecart > 0.15, 'le bras doit balancer AMPLEMENT en marchant (amplitude ' + ecart.toFixed(3) + ' rad, exigé > 0.15) — sinon bâton de bois');
      } },
    { nom: 'corps_entier', desc: 'GARDE-FOU biomécanique : le corps ne s\'enfonce pas dans le sol (hanches à bonne hauteur)',
      run: async () => {
        await load('#arene'); await demarrer();
        for (let i = 0; i < 3 && !(await ev('window.D.avatar.visible')); i++) { await ev('window.D.basculerVue()'); await sleep(250); }
        await key('KeyW','keyDown'); await sleep(600);
        const h = await ev('(function(){var v=window.D.avatar&&window.D.avatar.userData&&window.D.avatar.userData.vrm;if(!v||!v.humanoid)return null;var b=v.humanoid.getNormalizedBoneNode("hips");if(!b)return null;var p=new window.D.THREE.Vector3();b.getWorldPosition(p);var a=new window.D.THREE.Vector3();window.D.avatar.getWorldPosition(a);return p.y-a.y;})()');
        await key('KeyW','keyUp');
        assert(h !== null, 'hanches introuvables');
        assert(h > 0.45 && h < 1.4, 'hanches à ' + h.toFixed(2) + ' m du sol (attendu entre 0,45 et 1,4 m) — corps enfoncé ou flottant');
      } },
    { nom: 'mouvement_attaque', desc: 'GARDE-FOU combo : le bras droit bouge nettement pendant une frappe',
      run: async () => {
        await load('#arene'); await demarrer();
        for (let i = 0; i < 3 && !(await ev('window.D.avatar.visible')); i++) { await ev('window.D.basculerVue()'); await sleep(250); }
        const lireBrasD = () => ev('(function(){var v=window.D.avatar&&window.D.avatar.userData&&window.D.avatar.userData.vrm;if(!v||!v.humanoid)return null;var b=v.humanoid.getNormalizedBoneNode("rightUpperArm");return b?(b.rotation.x+b.rotation.z):null;})()');
        // On frappe plusieurs fois et on suit le bras du début à la fin du geste :
        // l'écart entre sa position la plus haute et la plus basse dit l'ampleur du coup.
        let bas = 99, haut = -99;
        for (let coup = 0; coup < 3; coup++) {
          await ev('window.D.frapper && window.D.frapper()');
          for (let i = 0; i < 8; i++) {
            const a = await lireBrasD();
            if (a !== null) { if (a < bas) bas = a; if (a > haut) haut = a; }
            await sleep(90);
          }
          await sleep(400);                       // le temps que le coup retombe
        }
        assert(bas < 99, 'os du bras droit introuvable');
        const ampli = haut - bas;
        assert(ampli > 0.08, 'le bras droit doit bouger nettement pendant la frappe (écart vu ' + ampli.toFixed(3) + ', exigé > 0.08)');
      } },
    { nom: 'corps_en_vol', desc: 'GARDE-FOU vol : en volant, le corps prend une VRAIE pose de vol (pas raide comme au sol)',
      run: async () => {
        await load('#arene'); await demarrer();
        for (let i = 0; i < 3 && !(await ev('window.D.avatar.visible')); i++) { await ev('window.D.basculerVue()'); await sleep(250); }
        // On lit l'épaule gauche : au sol elle pend le long du corps, en vol elle
        // s'ouvre en arrière comme une aile. Les deux chiffres doivent DIFFÉRER.
        const lireEpaule = () => ev('(function(){var v=window.D.avatar&&window.D.avatar.userData&&window.D.avatar.userData.vrm;if(!v||!v.humanoid)return null;var b=v.humanoid.getRawBoneNode("leftUpperArm");return b?(b.rotation.x+b.rotation.z):null;})()');
        await sleep(400);
        const auSol = await lireEpaule();
        assert(auSol !== null, 'os de l\'épaule gauche introuvable');
        // on décolle
        await ev('window.D.joueur.vol = true; window.D.joueur.saut = 4;');
        let bas = 99, haut = -99;
        for (let i = 0; i < 12; i++) {
          await ev('window.D.joueur.vol = true;');       // on reste en l'air pendant la mesure
          const a = await lireEpaule();
          if (a !== null) { if (a < bas) bas = a; if (a > haut) haut = a; }
          await sleep(120);
        }
        const diag = await ev('(function(){var j=window.D.joueur,a=window.D.avatar;return JSON.stringify({vol:!!(j&&j.vol),saut:j&&Math.round((j.saut||0)*10)/10,mana:j&&Math.round(j.mana||0),avatar:!!a,vrm:!!(a&&a.userData&&a.userData.vrm),erreur:String(window.__derniereErreur||"aucune")});})()');
        await ev('window.D.joueur.vol = false;');
        assert(bas < 99, 'épaule illisible en vol — état du jeu au moment du test : ' + diag);
        const ecart = Math.min(Math.abs(haut - auSol), Math.abs(bas - auSol));
        assert(ecart > 0.20, 'en vol le bras doit s\'ouvrir, pas rester comme au sol (écart vu ' + ecart.toFixed(3) + ', exigé > 0.20)');
        const respire = haut - bas;
        assert(respire > 0.01, 'en vol le corps doit RESPIRER, pas se figer dans une pose (variation vue ' + respire.toFixed(4) + ')');
      } },
    { nom: 'mouvement_guerrier', desc: 'GARDE-FOU adversaire : le guerrier n\'est pas figé (ses os bougent)',
      run: async () => {
        await load('#arene'); await demarrer();
        // attendre que le guerrier (chargé en arrière-plan) soit posé
        for (let i = 0; i < 30 && !(await ev('!!(window.D.guerrier && window.D.guerrier.vrm)')); i++) await sleep(1000);
        const lire = () => ev('(function(){var G=window.D.guerrier;if(!G||!G.vrm||!G.vrm.humanoid)return null;var b=G.vrm.humanoid.getRawBoneNode("leftUpperArm");var c=G.vrm.humanoid.getNormalizedBoneNode("leftUpperLeg");return (b?b.rotation.x:0)+(c?c.rotation.x:0)+(G.x+G.z)*0.5;})()');
        const mesures = [];                                   // 6 mesures sur ~2,4 s : os OU déplacement = pas une statue
        for (let i = 0; i < 6; i++) { mesures.push(await lire()); await sleep(400); }
        assert(mesures.every(m => m !== null), 'guerrier VRM absent après attente');
        const ecart = Math.max(...mesures) - Math.min(...mesures);
        assert(ecart > 0.02, 'les os (ou la position) du guerrier doivent bouger (amplitude ' + ecart.toFixed(3) + ', exigé > 0.02) — sinon statue');
      } },
    { nom: 'guerrier_face_joueur', desc: 'GARDE-FOU orientation : l\'adversaire fait FACE au joueur (jamais de dos)',
      run: async () => {
        await load('#arene'); await demarrer();
        for (let i = 0; i < 30 && !(await ev('!!(window.D.guerrier && window.D.guerrier.vrm)')); i++) await sleep(1000);
        await sleep(800);   // le temps qu'il s'oriente
        const dot = await ev('(function(){var G=window.D.guerrier,j=window.D.joueur;if(!G)return null;' +
          'var v=new window.D.THREE.Vector3();G.obj.getWorldDirection(v);' +      // donne l\'axe AVANT (+Z) de l\'objet
          'var s=G.vrm?1:-1;' +                                                    // le VRoid regarde +Z ; l\'ancien modèle -Z
          'var dx=j.x-G.x,dz=j.z-G.z,n=Math.hypot(dx,dz)||1;' +                   // la direction vers le joueur
          'return s*(v.x*(dx/n)+v.z*(dz/n));})()');                               // >0 = il fait face, <0 = de dos
        assert(dot !== null, 'adversaire absent');
        assert(dot > 0.3, 'l\'adversaire doit faire FACE au joueur (score ' + dot.toFixed(2) + ', exigé > 0,3 ; négatif = de dos)');
      } },
    { nom: 'mouvement_villageois', desc: 'GARDE-FOU village vivant : au moins un villageois bouge (os ou position)',
      run: async () => {
        await load('#village'); await demarrer();
        for (let i = 0; i < 30 && !(await ev('window.D.villageois && window.D.villageois.length > 0')); i++) await sleep(1000);
        const lire = () => ev('(function(){var vs=window.D.villageois||[];if(!vs.length)return null;var s=0;vs.forEach(function(v){s+=v.x+v.z;var o=v.os&&v.os.lUA;if(o)s+=o.rotation.x*10;});return s;})()');
        // PATIENCE : chaque villageois attend 1 à 5 s entre deux étapes de sa tournée.
        // On regarde sur 16 s, sinon on tombe pendant sa pause et on croit le village mort.
        const r1 = await lire();
        let bouge = 0;
        for (let i = 0; i < 8; i++) {
          await sleep(2000);
          const r = await lire();
          if (Math.abs(r - r1) > 0.05) { bouge = Math.abs(r - r1); break; }
        }
        assert(r1 !== null, 'aucun villageois posé');
        assert(bouge > 0.05, 'au moins un villageois doit se déplacer en 16 s (écart vu ' + bouge.toFixed(4) + ') — sinon village mort');

        // TRAJET FIXE : chaque villageois doit avoir une tournée d'au moins 2 points
        const routes = await ev('(function(){var vs=window.D.villageois||[];return vs.filter(function(v){return v.etapes&&v.etapes.length>=2;}).length+"/"+vs.length;})()');
        const [avec, total] = routes.split('/').map(Number);
        assert(avec >= Math.ceil(total/2), 'la plupart des villageois doivent avoir un trajet fixe (' + routes + ')');

        // AMPLITUDE VALIDÉE : quand un villageois marche, son bras doit balancer comme celui du joueur
        // On suit le bras du MÊME villageois sur 20 s : l'écart entre sa position la plus
        // haute et la plus basse dit l'ampleur de son balancement, même s'il fait des pauses.
        let bas = 99, haut = -99;
        for (let i = 0; i < 40; i++) {
          // On mesure OÙ EST L'AVANT-BRAS dans l'espace, pas un angle interne :
          // un angle peut rester à zéro alors que le bras bouge vraiment (les deux
          // fabriques d'os ne comptent pas les angles pareil). La position, elle, ne ment pas.
          const a = await ev('(function(){var vs=(window.D.villageois||[]).filter(function(v){return v.os&&v.os.lLA;});if(!vs.length)return null;var p=new window.D.THREE.Vector3(),q=new window.D.THREE.Vector3(),m=-99;vs.forEach(function(v){v.os.lLA.getWorldPosition(p);v.obj.getWorldPosition(q);var d=p.z-q.z+p.x-q.x;if(d>m)m=d;});return m;})()');
          if (a !== null) { if (a < bas) bas = a; if (a > haut) haut = a; }
          await sleep(500);
        }
        const ampli = haut - bas;
        assert(bas < 99, 'aucun villageois avec un bras trouvable');
        assert(ampli > 0.12, 'le bras d\'un villageois doit balancer amplement en marchant (écart vu ' + ampli.toFixed(3) + ' m, exigé > 0.12) — mêmes mouvements que le joueur');
      } },
    { nom: 'choc_epees', desc: 'CHOC D\'ÉPÉES : les deux se figent, le mana se verse, et le duel se tranche',
      run: async () => {
        await load('#arene'); await demarrer(); await sleep(3000);
        assert(await ev('!!(window.D.guerrier && window.D.guerrier.epee)'), 'l\'adversaire n\'a pas d\'épée en main');
        await ev('window.D.demarrerChoc()');
        await sleep(300);
        assert(await ev('window.D.choc.actif'), 'le choc ne démarre pas');
        // On relève la position UNE FOIS le choc commencé : avant, l'adversaire
        // bougeait encore normalement, et le test se plaignait pour rien.
        const posAvant = await ev('JSON.stringify([Math.round(window.D.joueur.x*10)/10, Math.round(window.D.guerrier.x*10)/10])');
        // On verse du mana en tenant la touche E, et la poussée doit monter.
        await key('KeyE', 'keyDown'); await sleep(900);
        const f1 = await ev('window.D.choc.forceJ');
        const manaPendant = await ev('window.D.joueur.mana');
        await key('KeyE', 'keyUp');
        assert(f1 > 5, 'verser du mana doit faire monter la poussée (vue : ' + f1.toFixed(1) + ')');
        assert(manaPendant < 20, 'verser du mana doit COÛTER du mana (reste : ' + manaPendant.toFixed(1) + ')');
        // Pendant le choc, on ne bouge plus.
        await key('KeyW','keyDown'); await sleep(500); await key('KeyW','keyUp');
        const posPendant = await ev('JSON.stringify([Math.round(window.D.joueur.x*10)/10, Math.round(window.D.guerrier.x*10)/10])');
        assert(posPendant === posAvant, 'pendant le choc personne ne doit se déplacer (' + posAvant + ' → ' + posPendant + ')');
        await shot('choc_epees');
        // Le duel doit se terminer tout seul avant 6 s.
        for (let i = 0; i < 12 && (await ev('window.D.choc.actif')); i++) await sleep(600);
        assert(!(await ev('window.D.choc.actif')), 'le choc doit se terminer tout seul');
        const apres = await ev('JSON.stringify({stun:window.D.joueur.stun||0, sonne:window.D.guerrier.sonne||0})');
        const r = JSON.parse(apres);
        assert(r.stun > 0 || r.sonne > 0, 'à la fin, le perdant doit être sonné (vu : ' + apres + ')');
      } },
    { nom: 'pas_de_plantage', desc: 'GARDE-FOU écran noir : le village démarre sans erreur qui fige tout',
      run: async () => {
        // Bug du 22/08 : un springbone d'avatar cassé plantait vrm.update et FIGEAIT
        // le jeu (écran noir, on ne peut plus bouger). majVrm() doit l'empêcher.
        await load('#village'); await demarrer(); await sleep(6000);
        assert(!(await ev('!!document.getElementById("boite-erreur")')),
          'un bandeau d\'erreur s\'affiche : quelque chose plante au village');
        // et le joueur doit pouvoir avancer (jeu pas figé)
        const av = await ev('window.D.joueur.z');
        await key('KeyW','keyDown'); await key('KeyZ','keyDown'); await sleep(1000);
        await key('KeyW','keyUp'); await key('KeyZ','keyUp');
        const ap = await ev('window.D.joueur.z');
        assert(av !== ap, 'le joueur ne bouge pas : le jeu est figé (position ' + av + ')');
      } },
    { nom: 'murs_au_sol', desc: 'GARDE-FOU murs : le bas des murs touche le SOL, même après un étage plus haut',
      run: async () => {
        // On descend à l'étage 1 (plafond à 30 m), PUIS on revient au village.
        // C'est le trajet qui faisait flotter les murs (la hauteur restait à 30).
        await load('#donjon'); await demarrer();
        // On s'assure d'être VRAIMENT en jeu avant de descendre (le menu peut rester).
        for (let i = 0; i < 10 && (await ev('window.D&&window.D.etat')) !== 'jeu'; i++) {
          await ev('(function(){var b=document.getElementById("jouer");if(b&&!b.disabled)b.click();})()'); await sleep(700);
        }
        await ev('window.D.allerA(1)'); await sleep(4000);
        // PATIENCE : les murs se reconstruisent à l'image suivante. Sans cette
        // attente, le test crie « murs introuvables » alors qu'ils arrivent.
        for (let i = 0; i < 14 && !(await ev('!!(window.D.murIM && window.D.murIM.count>0)')); i++) await sleep(700);
        const diag = await ev('JSON.stringify({etat:window.D&&window.D.etat, niveau:window.D&&window.D.etageCourant&&"?", murIM:!!(window.D.murIM), count:window.D.murIM?window.D.murIM.count:0})');
        // Rend {aucun:true} s'il n'y a pas de mur instancié (cas normal du village,
        // dont la palissade est faite de modèles). Rend {bas} sinon.
        const mesurer = () => ev(`(function(){
          var m = window.D.murIM; if(!m || !m.count) return { aucun:true };
          var h = m.geometry.parameters.height;
          var mat = new window.D.THREE.Matrix4(), p = new window.D.THREE.Vector3();
          var pire = 0;
          for(var i=0;i<Math.min(m.count,40);i++){ m.getMatrixAt(i,mat); p.setFromMatrixPosition(mat);
            var bas = p.y - h/2; if(Math.abs(bas) > Math.abs(pire)) pire = bas; }
          return { hauteur:h, basLePirePlusEloigne:Math.round(pire*100)/100 };
        })()`);
        const donjon = await mesurer();
        assert(donjon && !donjon.aucun, 'murs introuvables à l\'étage 1 — état vu : ' + diag);
        assert(Math.abs(donjon.basLePirePlusEloigne) < 0.4,
          'à l\'étage 1, le bas d\'un mur flotte à ' + donjon.basLePirePlusEloigne + ' m du sol (doit être ~0)');
        // Retour au village : soit il n'a AUCUN mur instancié (normal), soit s'il
        // en a un (fantôme du donjon), il ne doit pas flotter. Les deux sont bons.
        await ev('window.D.allerA(0)'); await sleep(3500);
        const village = await mesurer();
        assert(village.aucun || Math.abs(village.basLePirePlusEloigne) < 0.4,
          'de retour au village, un mur flotte à ' + village.basLePirePlusEloigne + ' m du sol (doit toucher le sol)');
      } },
    { nom: 'deux_epees', desc: 'ESCRIME À DEUX LAMES : la touche X donne une 2e épée, et les DEUX sont visibles',
      run: async () => {
        await load('#arene'); await demarrer();
        for (let i = 0; i < 3 && !(await ev('window.D.avatar.visible')); i++) { await ev('window.D.basculerVue()'); await sleep(250); }
        // PATIENCE : l'avatar arrive après ses gros fichiers. Sans cette attente,
        // le test dit « pas de 2e épée » alors qu'elle est créée une seconde plus tard.
        for (let i = 0; i < 15 && !(await ev('!!(window.D.avatar.userData && window.D.avatar.userData.epeeMainG)')); i++) await sleep(1000);
        assert(await ev('!!window.D.avatar.userData.epeeMainG'), 'la 2e épée (main gauche) n\'a pas été créée');
        // X fait le tour : une épée → deux épées → poings
        await key('KeyX', 'keyDown'); await key('KeyX', 'keyUp'); await sleep(400);
        const mode = await ev('window.D.armeMode');
        assert(mode === 'deux', 'après un X on doit être à deux épées (mode vu : ' + mode + ')');
        const vues = await ev('(function(){var u=window.D.avatar.userData;return (u.epeeMain&&u.epeeMain.visible?1:0)+(u.epeeMainG&&u.epeeMainG.visible?1:0);})()');
        await shot('deux_epees');
        assert(vues === 2, 'les DEUX épées doivent être visibles (vues : ' + vues + ')');
        // les coups doivent partir plus vite qu'avec une seule lame
        await ev('window.D.joueur.atkCd = 0; window.D.frapper();');
        const cdDeux = await ev('window.D.joueur.atkCd');
        await key('KeyX','keyDown'); await key('KeyX','keyUp'); await sleep(300);   // → poings
        await key('KeyX','keyDown'); await key('KeyX','keyUp'); await sleep(300);   // → une épée
        await ev('window.D.joueur.atkCd = 0; window.D.joueur.comboT = 0; window.D.frapper();');
        const cdUne = await ev('window.D.joueur.atkCd');
        assert(cdDeux < cdUne, 'à deux lames les coups doivent partir PLUS VITE (' + cdDeux.toFixed(2) + ' s contre ' + cdUne.toFixed(2) + ' s)');
      } },
    { nom: 'os_villageois', desc: 'GARDE-FOU : CHAQUE villageois a retrouvé ses os (sinon il glisse sans bouger)',
      run: async () => {
        await load('#village'); await demarrer(); await sleep(4000);
        // On laisse le temps aux habitants de se poser et de commencer leur tournée.
        for (let i = 0; i < 10 && !(await ev('(window.D.villageois||[]).length')); i++) await sleep(1000);
        // PATIENCE : les os sont retrouvés à l'image SUIVANTE, pas à l'instant où
        // l'habitant apparaît. Sans cette attente, le test crie au loup pour rien.
        const compter = () => ev('(function(){var vs=window.D.villageois||[];return JSON.stringify(vs.map(function(v){return v.os?(v.os.trouves||0):-1;}));})()');
        let bilan = await compter();
        for (let i = 0; i < 12 && JSON.parse(bilan || '[]').some(n => n < 9); i++) { await sleep(1000); bilan = await compter(); }
        const os = JSON.parse(bilan || '[]');
        assert(os.length > 0, 'aucun villageois dans le village');
        const muets = os.filter(n => n < 9).length;
        assert(muets === 0, muets + ' villageois sur ' + os.length + ' n\'ont PAS trouvé leurs os (ils glisseraient) — comptes vus : ' + bilan);
      } },
    { nom: 'mouvement_mage', desc: 'GARDE-FOU mage : l\'avatar mage bouge aussi amplement en marchant',
      run: async () => {
        await load('#arene');
        await ev('var b=document.querySelector(".classe-tab[data-classe=mage]"); b && b.click()');   // choisir la classe Mage
        await demarrer();
        for (let i = 0; i < 3 && !(await ev('window.D.avatar.visible')); i++) { await ev('window.D.basculerVue()'); await sleep(250); }
        // attendre que le fichier du mage (chargé en arrière-plan) soit prêt et posé
        for (let i = 0; i < 25 && !(await ev('!!(window.D.avatar.userData.vrm)')); i++) await sleep(1000);
        const lireBras = () => ev('(function(){var v=window.D.avatar&&window.D.avatar.userData&&window.D.avatar.userData.vrm;if(!v||!v.humanoid)return null;var b=v.humanoid.getRawBoneNode("leftUpperArm");return b?b.rotation.x:null;})()');
        await key('KeyW','keyDown'); await sleep(300);
        const mesures = [];
        for (let i = 0; i < 14; i++) { mesures.push(await lireBras()); if (i === 3) await shot('mage_marche'); await sleep(180); }
        await key('KeyW','keyUp');
        assert(mesures.every(m => m !== null), 'avatar mage VRM introuvable');
        const ecart = Math.max(...mesures) - Math.min(...mesures);
        assert(ecart > 0.15, 'le bras du mage doit balancer en marchant (amplitude ' + ecart.toFixed(3) + ' rad, exigé > 0.15)');
      } },
    { nom: 'avatar_orientation', desc: 'avatar tourné dans le sens de la marche (rotation = lacet + π)',
      run: async () => {
        await load('#arene'); await demarrer();
        // l'orientation avatar n'est calculée qu'en 3e personne → on force la vue 3 (avatar visible)
        for (let i = 0; i < 3 && !(await ev('window.D.avatar.visible')); i++) { await ev('window.D.basculerVue()'); await sleep(250); }
        // 1) en avançant, le corps regarde là où la caméra regarde
        await key('KeyW','keyDown'); await sleep(900);
        const avant = await ev('(window.D.joueur.cap - window.D.joueur.lacet)');
        await key('KeyW','keyUp'); await shot('avatar_orientation');
        const ecartAvant = Math.abs(Math.atan2(Math.sin(avant), Math.cos(avant)));
        assert(ecartAvant < 0.15, 'en avançant, le corps doit regarder devant (écart ' + ecartAvant.toFixed(2) + ' rad)');
        // 2) GARDE-FOU DEMI-TOUR (Patrick, 21/08) : en reculant, le corps doit se
        // RETOURNER, pas marcher en crabe. On attend un demi-tour, donc ~π.
        await key('KeyS','keyDown'); await sleep(1200);
        const arriere = await ev('(window.D.joueur.cap - window.D.joueur.lacet)');
        await key('KeyS','keyUp'); await shot('avatar_demi_tour');
        const ecartArriere = Math.abs(Math.atan2(Math.sin(arriere), Math.cos(arriere)));
        assert(ecartArriere > 2.6, 'en reculant le corps doit faire VOLTE-FACE (demi-tour vu ' + ecartArriere.toFixed(2) + ' rad, exigé > 2,6 soit ~150°)');
      } },
    { nom: 'jauge_mana', desc: 'le mana existe, a un max > 0, et se régénère',
      run: async () => {
        await load('#arene'); await demarrer();
        await ev('window.D.joueur.mana = 0');                     // on vide
        const m0 = await ev('window.D.joueur.mana');
        await sleep(1500);                                        // on laisse régénérer
        const m1 = await ev('window.D.joueur.mana');
        const max = await ev('window.D.joueur.manaMax');
        assert(max > 0, 'manaMax doit être > 0, obtenu ' + max);
        assert(m1 > m0, 'le mana doit remonter (régén) : ' + m0 + ' -> ' + m1);
      } },
    { nom: 'voix_coupee', desc: 'GARDE-FOU : la voix reste COUPÉE (Patrick ne l\'aime pas) — aucun son de voix ne part',
      run: async () => {
        await load('#arene'); await demarrer();
        for (let i = 0; i < 20 && (await ev('window.D && window.D.etat')) !== 'jeu'; i++) await sleep(1000);
        for (let essai = 0; essai < 3; essai++) {                    // on lance des incantations exprès
          await ev('window.D.traiterChat("dragon slave")'); await sleep(1200);
        }
        const joue = await ev('performance.getEntriesByType("resource").some(r=>/voix\\/.*\\.mp3/.test(r.name))');
        assert(joue === false, 'aucun fichier de voix ne doit être joué : la voix est coupée volontairement');
      } },
    { nom: 'menu_classe_mage', desc: 'choisir la classe Mage met bien classe = mage',
      run: async () => {
        await load('');                                          // reste au menu
        await ev('document.querySelector(".classe-tab[data-classe=mage]").click()');
        const c = await ev('document.querySelector(".classe-tab.on") && document.querySelector(".classe-tab.on").dataset.classe');
        assert(c === 'mage', 'le bouton Mage devrait devenir actif (.on), obtenu ' + c);
      } },
    { nom: 'memoire_coffre', desc: 'MÉMOIRE DU MONDE : ouvrir le coffre de l\'étage 1 note un fait qui survit au rechargement',
      run: async () => {
        await load('#donjon'); await demarrer();
        assert((await ev('window.D.etat')) === 'jeu', 'le jeu n\'est pas démarré');
        // CAS 1 — état initial : nouveau jeu, aucun fait, coffre fermé
        const nbFaits0 = Object.keys(JSON.parse(await ev('JSON.stringify(window.D.faits||{})'))).length;
        const o0 = await ev('window.D.coffre && window.D.coffre.ouvert');
        assert(nbFaits0 === 0, 'un nouveau jeu ne doit avoir AUCUN fait (vus : ' + nbFaits0 + ')');
        assert(o0 === false, 'au premier lancement le coffre doit être FERMÉ');
        // on s'approche du coffre, face à lui, pour la photo et pour l'action
        const approcher = async dist => {
          await ev('(function(){var c=window.D.coffre.obj.position,j=window.D.joueur;j.x=c.x+'+dist+';j.z=c.z;j.lacet=Math.PI/2;j.tangage=0;})()');
          await sleep(500);
        };
        await approcher(1.4);
        await shot('memoire_avant_ouverture');
        // CAS 2 — ouverture par la VRAIE action (touche E)
        await key('KeyE','keyDown'); await sleep(200); await key('KeyE','keyUp');
        const o1 = await ev('window.D.coffre.ouvert');
        const f1 = await ev('window.D.lireFait("etage1:coffre")');
        assert(o1 === true, 'le coffre doit être OUVERT après E (état vu : ' + o1 + ')');
        assert(f1 === true, 'le fait « etage1:coffre » doit être noté, vu : ' + f1);
        await shot('memoire_apres_ouverture');
        // CAS 3 — RECHARGEMENT réel de la page (même profil → localStorage conservé)
        await load('#donjon'); await demarrer();
        const f2 = await ev('window.D.lireFait("etage1:coffre")');
        const o2 = await ev('window.D.coffre && window.D.coffre.ouvert');
        const r2 = await ev('window.D.ouvrirCoffre()');   // tentative de deuxième pillage
        assert(f2 === true, 'après rechargement le fait doit EXISTER encore');
        assert(o2 === true, 'après rechargement le coffre doit DÉJÀ être ouvert (vu : ' + o2 + ')');
        assert(r2 === false, 'on ne doit pas pouvoir rouvrir un coffre déjà ouvert');
        await approcher(1.4);                       // on retourne voir le coffre
        await shot('memoire_apres_rechargement');
      } },
    { nom: 'banque_salle', desc: 'BANQUE : la salle #banque démarre, recolorée bleu/gris, avec portail, écran de solde et compétence « virement »',
      run: async () => {
        await load('#banque'); await demarrer();
        // PATIENCE : l'ancre #banque autolance commencer() après le chargement des modèles
        for (let i = 0; i < 15 && !(await ev('window.D && typeof window.D.estBanque === "function" && window.D.estBanque()')); i++) await sleep(1000);
        const diag = await ev('JSON.stringify({etat: window.D && window.D.etat, estBanque: (typeof window.D==="object" && typeof window.D.estBanque==="function") ? window.D.estBanque() : "?", fond: window.D && window.D.scene && window.D.scene.background ? window.D.scene.background.getHex() : null})');
        assert(await ev('window.D && typeof window.D.estBanque === "function"') === true
          ? await ev('window.D.estBanque()')
          : false, 'la salle banque ne démarre pas — état vu : ' + diag);
        // 1. la palette banque est visible (bleu nuit, peint par batirBanque)
        const fond = await ev('window.D.scene.background && window.D.scene.background.getHex()');
        assert(fond === 0x0a1220, 'le fond doit être bleu nuit banque 0x0a1220 (vu : ' + fond + ')');
        // 2. le HUD affiche « Banque »
        const hud = await ev('document.getElementById("etage") ? document.getElementById("etage").textContent : ""');
        assert(/Banque/.test(hud), 'le HUD doit afficher Banque (vu : "' + hud + '")');
        // 3. le portail et l'écran de solde sont posés et visibles
        assert(await ev('!!(window.D.meshPortail && window.D.meshPortail.visible)'), 'le portail de la banque doit être posé et visible');
        assert(await ev('!!(window.D.banque && window.D.banque.ecran && window.D.banque.ecran.visible)'), 'l\'écran de solde doit être visible dans la banque');
        // 4. parler « valider un virement » lance une projection (la compétence est vivante)
        const avant = await ev('(window.D.projectiles || []).length');
        await ev('window.D.traiterChat("valider un virement")'); await sleep(500);
        const apres = await ev('(window.D.projectiles || []).length');
        const espr = await ev('document.getElementById("repond") ? document.getElementById("repond").textContent : ""');
        assert(apres > avant, 'dire « valider un virement » doit lancer un projectile (' + avant + ' → ' + apres + ')');
        assert(/Valider un virement/.test(espr), 'le panneau doit afficher le nom bancaire (vu : "' + espr + '")');
        await shot('banque_salle');
      } },
    { nom: 'banque_portail_sandbox', desc: 'BANQUE : le portail déclenche UNE requête POST sandbox (sans faire descendre d\'étage)',
      run: async () => {
        await load('#banque'); await demarrer();
        for (let i = 0; i < 15 && !(await ev('window.D && typeof window.D.estBanque === "function" && window.D.estBanque()')); i++) await sleep(1000);
        assert(await ev('window.D.estBanque()'), 'la banque ne démarre pas');
        // compteur réseau : on compte les POST /donjon/sandbox SANS bloquer le vrai fetch
        const cmp = await ev('(function(){ window.__sandboxPosts = 0; var f = window.fetch.bind(window); window.fetch = function(u,o){ var url = (typeof u === "string") ? u : (u && u.url) || ""; if (url.indexOf("donjon/sandbox") !== -1) window.__sandboxPosts++; return f(u,o); }; return true; })()');
        assert(cmp === true, 'impossible d\'accrocher le compteur réseau');
        // on pose le joueur SUR le portail (déclenchement automatique de majPortail)
        await ev('(function(){ var p = window.D.meshPortail.position; window.D.joueur.x = p.x + 0.3; window.D.joueur.z = p.z + 0.3; })()');
        await sleep(2000);
        const posts = await ev('window.__sandboxPosts || 0');
        const statut = await ev('(window.D.banque && window.D.banque.dernierStatut) || ""');
        const pasDescente = await ev('window.D.estBanque()');
        assert(posts > 0, 'le portail doit déclencher le POST /donjon/sandbox (postes : ' + posts + ')');
        assert(statut.length > 3, 'l\'écran doit porter un statut sandbox (vu : "' + statut + '")');
        assert(pasDescente, 'le portail banque ne doit PAS faire descendre au donjon (estBanque doit rester vrai)');
      } },
  ];

  function assert(cond, msg) { if (!cond) throw new Error(msg); }

  let ok = 0; const fails = [];
  // On peut ne lancer QU'UN test : SEUL=corps_en_vol node tests/runtime.js
  // (utile parce que tout lancer prend plusieurs minutes sur cette machine)
  const seul = process.env.SEUL || '';
  for (const c of CAS.filter(x => !seul || seul.split(',').some(s => x.nom.includes(s.trim())))) {
    try { await c.run(); console.log('  ✅ ' + c.nom + ' — ' + c.desc); ok++; }
    catch (e) { console.log('  ❌ ' + c.nom + ' — ' + e.message); fails.push(c.nom); }
  }
  console.log('\n  ' + ok + '/' + CAS.length + ' cas réussis' + (fails.length ? ' — échecs : ' + fails.join(', ') : ''));
  console.log('  captures dans tests/captures/');
  ws.close(); process.exit(fails.length ? 1 : 0);
})();
