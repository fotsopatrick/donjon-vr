// SONDE TRADUCTION DU CHAT — les 10 points demandés pour la feature :
// FR→JA, texte original conservé, message vide, caractères japonais, noms
// propres, erreur du service, timeout, cache, absence de clé, chat normal.
// Usage : node tests/sonde-traduction.js [port]
const http = require('http'), fs = require('fs');
const PORT = process.argv[2] || 9260;
const dodo = ms => new Promise(r => setTimeout(r, ms));
const getJSON = p => new Promise((r, j) =>
  http.get('http://127.0.0.1:' + PORT + p, x => { let d = ''; x.on('data', c => d += c); x.on('end', () => { try { r(JSON.parse(d)); } catch (e) { j(e); } }); }).on('error', j));

let echecs = 0;
const verifie = (nom, cond, detail) => {
  console.log((cond ? '  OK  ' : '  ÉCHEC ') + nom + (cond ? '' : ' — ' + (detail || '? ')));
  if (!cond) echecs++;
};
const EST_JAPONAIS = t => /[\u3040-\u30ff\u4e00-\u9faf]/.test(t || '');

(async () => {
  const page = (await getJSON('/json')).find(x => x.type === 'page' && x.webSocketDebuggerUrl);
  if (!page) { console.log('AUCUNE PAGE'); process.exit(2); }
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0; const att = {};
  const env = (m, p) => new Promise(r => { const i = ++id; att[i] = r; ws.send(JSON.stringify({ id: i, method: m, params: p || {} })); });
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && att[m.id]) { att[m.id](m.result || {}); delete att[m.id]; } };
  await new Promise(r => ws.onopen = r);
  await env('Runtime.enable'); await env('Page.enable');
  const lire = async x => { const r = await env('Runtime.evaluate', { expression: x, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) return 'ERREUR: ' + (r.exceptionDetails.exception && r.exceptionDetails.exception.description || r.exceptionDetails.text);
    return r.result && r.result.value; };

  await env('Page.navigate', { url: 'http://127.0.0.1:8099/index.html?t=' + Date.now() + '#village' });
  let modulePret = false;
  for (let i = 0; i < 90 && !modulePret; i++) { await dodo(1000); modulePret = !!(await lire('!!(window.Traduction && window.KOTOAGE)')); }
  verifie('TranslationService chargé (window.Traduction)', modulePret);
  let parti = false;
  for (let i = 0; i < 40 && !parti; i++) {
    await lire('(function(){var b=document.getElementById("jouer");if(b&&!b.disabled)b.click();})()');
    await dodo(1000);
    parti = (await lire('window.D&&window.D.etat')) === 'jeu';
  }
  verifie('jeu démarré (le chat répond)', parti);

  // 1. FR → JA (dictionnaire de secours : le serveur local ne tourne pas ici)
  const ja1 = await lire('window.Traduction.translate("Bonjour, vous allez bien ?", "fr", "ja")');
  verifie('1. FR→JA : phrase connue traduite', EST_JAPONAIS(ja1), 'vu « ' + ja1 + ' »');

  // 3. message vide → null, sans erreur
  verifie('3. message vide → null', (await lire('window.Traduction.translate("  ")')) === null);

  // 4. caractères japonais dans la sortie
  verifie('4. la sortie contient bien du japonais', EST_JAPONAIS(ja1));

  // 5. noms propres : inconnu → null (le français est gardé, rien n\'est cassé)
  verifie('5. noms propres : phrase inconnue → null (français conservé)',
    (await lire('window.Traduction.translate("Salut Kirito, ça roule ?")')) === null);

  // 6. erreur du service → repli sur le dictionnaire, sans plantage
  await lire('window.Traduction.purgerCache()');
  await lire('window.Traduction._serveur = async function(){ throw new Error("panne réseau"); }');
  const jaPanne = await lire('window.Traduction.translate("Merci beaucoup.", "fr", "ja")');
  verifie('6. erreur du service → repli dictionnaire (pas de plantage)', EST_JAPONAIS(jaPanne), 'vu « ' + jaPanne + ' »');

  // 7. timeout : un serveur qui ne répond jamais → repli après le délai
  await lire('window.Traduction.purgerCache()');
  await lire('window.Traduction._delaiMaxMs = 300');
  await lire('window.Traduction._serveur = function(){ return new Promise(function(){}); }');   // jamais résolu
  const jaTimeout = await lire('window.Traduction.translate("Je suis perdu.", "fr", "ja")');
  verifie('7. timeout → repli dictionnaire (300 ms)', EST_JAPONAIS(jaTimeout), 'vu « ' + jaTimeout + ' »');
  await lire('window.Traduction._delaiMaxMs = 4000');

  // 8. cache : une seule fois sur le serveur pour un même texte
  await lire('window.Traduction.purgerCache()');
  await lire('window.__compteServeur = 0');
  await lire('window.Traduction._serveur = function(){ window.__compteServeur++; return Promise.resolve(null); }');
  await lire('window.Traduction.translate("Au revoir.", "fr", "ja")');
  await lire('window.Traduction.translate("Au revoir.", "fr", "ja")');   // 2e appel → cache
  await lire('window.Traduction.translate("Au revoir.", "fr", "ja")');   // 3e appel → cache
  verifie('8. cache : 1 seul appel serveur pour 3 demandes identiques',
    (await lire('window.__compteServeur')) === 1, 'appels = ' + await lire('window.__compteServeur'));

  // 9 + 2. absence de clé / service absent → le chat garde le français, rien ne casse
  await lire('window.Traduction.purgerCache()');
  await lire('window.Traduction._serveur = function(){ return Promise.reject(new Error("connexion refusée")); }');
  const jaSansCle = await lire('window.Traduction.translate("Bonne nuit.", "fr", "ja")');
  verifie('9. absence de service → repli, chat intact', EST_JAPONAIS(jaSansCle));

  // 10. bout en bout dans le vrai chat : on écrit en français, le japonais s\'ajoute
  await lire('window.Traduction.purgerCache()');
  await lire('window.Traduction._serveur = function(){ return Promise.resolve(null); }');   // pas de serveur : dictionnaire
  await lire('window.D.traiterChat("Bonjour ! Bienvenue dans mon monde.")');
  // le français reste affiché dans #entendu
  verifie('2. le texte original (français) reste affiché',
    (await lire('document.getElementById("entendu").textContent')) === '« Bonjour ! Bienvenue dans mon monde. »');
  let tra = '';
  for (let i = 0; i < 20 && !EST_JAPONAIS(tra); i++) { await dodo(300); tra = await lire('document.getElementById("traduction").textContent'); }
  verifie('10. le chat affiche 🇯🇵 + japonais en dessous du français',
    /🇯🇵/.test(tra) && EST_JAPONAIS(tra), 'traduction : « ' + tra + ' »');

  verifie('aucune erreur écran', (await lire('!document.getElementById("boite-erreur")')) === true);

  const { data } = await env('Page.captureScreenshot', { format: 'png' });
  fs.mkdirSync(__dirname + '/captures', { recursive: true });
  fs.writeFileSync(__dirname + '/captures/traduction_ja.png', Buffer.from(data, 'base64'));
  console.log('PHOTO : tests/captures/traduction_ja.png');

  ws.close();
  console.log(echecs ? 'Résultat : ' + echecs + ' échec(s)' : 'Résultat : 0 échec');
  process.exit(echecs ? 1 : 0);
})();
