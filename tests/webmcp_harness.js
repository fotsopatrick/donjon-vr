// =====================================================================
//  Harnais de test — exécute webmcp/webmcp.js dans Node.
// ---------------------------------------------------------------------
//  Utilisé par tests/test_webmcp.py : chaque appel Python démarre un
//  process Node jetable (état neuf = tests déterministes), lui demande
//  d'exécuter un outil (ou une séquence), et lit la réponse JSON sur
//  stdout. Aucun navigateur, aucun WebGL : respect de la règle nº1
//  (« ne pas faire ronfler nomi »).
//
//  Modes :
//    node tests/webmcp_harness.js __liste_outils__
//    node tests/webmcp_harness.js __schema__        '{"name":"..."}'
//    node tests/webmcp_harness.js <tool>            '{"x":0,"z":1}'
//    node tests/webmcp_harness.js __sequence__      '[{"tool":"dig","args":{}}, ...]'
// =====================================================================
const { creerControleurWebMCP, ETAT_INITIAL } = require("../webmcp/webmcp.js");

const [, , mode, argJson] = process.argv;
const payload = argJson ? JSON.parse(argJson) : {};

// Faux document.modelContext : il ENREGISTRE tout ce qu'on lui donne.
// C'est lui qui porte l'information « quels outils existent » que les
// tests Python inspectent.
const registre = {};
const modelContext = {
  registerTool(d) {
    registre[d.name] = d;
    return true;
  },
};

// État de jeu de test : copie propre de l'état factice (la grille est un
// tableau imbriqué → il faut le cloner à la main).
const etat = { ...ETAT_INITIAL, grille: ETAT_INITIAL.grille.map((ligne) => ligne.slice()) };

creerControleurWebMCP({ modelContext, etat });

// Les exécutions d'outils sont async par contrat WebMCP.
(async () => {
  if (mode === "__liste_outils__") {
    process.stdout.write(JSON.stringify(Object.keys(registre)));
    return;
  }
  if (mode === "__schema__") {
    const outil = registre[payload.name];
    process.stdout.write(JSON.stringify(outil ? outil.inputSchema : null));
    return;
  }
  if (mode === "__champ__") {
    const valeur = etat[payload.cle];
    process.stdout.write(JSON.stringify(valeur === undefined ? null : valeur));
    return;
  }
  if (mode === "__sequence__") {
    const resultats = [];
    for (const { tool, args } of payload.steps || payload) {
      const outil = registre[tool];
      resultats.push(outil ? await outil.execute(args || {}) : { ok:false, message:"outil inconnu : " + tool });
    }
    // Le harnais peut renvoyer l'état d'après-séquence (même process = état vrai).
    const champs = {};
    if (payload.champs) for (const cle of payload.champs) champs[cle] = etat[cle];
    process.stdout.write(JSON.stringify(payload.champs ? { resultats, champs } : resultats));
    return;
  }
  const outil = registre[mode];
  if (!outil) {
    process.stdout.write(JSON.stringify({ ok: false, message: "outil inconnu : " + mode }));
    return;
  }
  process.stdout.write(JSON.stringify(await outil.execute(payload)));
})();

function echec(message) {
  return { ok: false, message };
}