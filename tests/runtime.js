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
    { nom: 'deux_epees', desc: 'ESCRIME À DEUX LAMES : la touche X donne une 2e épée, et les DEUX sont visibles',
      run: async () => {
        await load('#arene'); await demarrer();
        for (let i = 0; i < 3 && !(await ev('window.D.avatar.visible')); i++) { await ev('window.D.basculerVue()'); await sleep(250); }
        await sleep(1500);
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
