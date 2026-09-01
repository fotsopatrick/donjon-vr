// =====================================================================
//  Harnais d'INTÉGRATION — simule la page du jeu (window, document,
//  document.modelContext, __webmcpConnexion) puis charge
//  webmcp/integration.js (LE code du navigateur), et journalise chaque
//  effet de bord réel sur le « jeu ».
// ---------------------------------------------------------------------
//  Utilisé par tests/test_webmcp_integration.py. Un process par scénario,
//  état neuf à chaque fois. Aucun navigateur, aucun WebGL.
//
//  Modes (JSON ou texte sur argv[2]) :
//    {"action":"sans-contexte"}                  (texte : "sans-contexte")
//    {"action":"etat"}
//    {"action":"appel","tool":"...","args":{...}}
//    {"action":"sequence","steps":[{"tool":"...","args":{}}, ...]}
// =====================================================================
const API = require("../webmcp/webmcp.js");

globalThis.window = globalThis;

// ── Le « jeu » factice : mêmes noms que le pont réel (__webmcpConnexion).
const C = {
  joueur: { x: 0, z: 0, vie: 5, vieMax: 10, mana: 3, manaMax: 10, epee: true },
  niveau: 1,
  T: 2.6,
  grid: Array.from({ length: 18 }, (_, y) =>
    Array.from({ length: 28 }, (_, x) => (x === 0 || y === 0 || x === 27 || y === 17 ? 0 : 1)),
  ),
  torches: [],
  construireMurs() { journal.push("construireMurs"); },
  poserPiege(x, z) { journal.push(["poserPiege", x, z]); },
  dessinerCoeurs() { journal.push("dessinerCoeurs"); },
  dire(t) { journal.push(["dire", t]); },
  monte(type, x, z) { journal.push(["monte", type, +x.toFixed(2), +z.toFixed(2)]); },
};

const journal = (globalThis.__journal = []);
window.KOTOAGE_WEBMCP = API;
window.__webmcpConnexion = C;

const brut = process.argv[2] || '{"action":"etat"}';
const req = brut === "sans-contexte" ? { action: "sans-contexte" } : JSON.parse(brut);
const rep = (x) => process.stdout.write(JSON.stringify(x));

if (req.action === "sans-contexte") {
  // Pas de document.modelContext : l'intégration doit rester muette.
  globalThis.document = {};
  require("../webmcp/integration.js");
  rep({ muet: window.__webmcpActif === undefined, journal });
  process.exit(0);
}

const modelContext = {
  regs: {},
  registerTool(d) { this.regs[d.name] = d; return true; },
};
globalThis.document = { modelContext };
require("../webmcp/integration.js");

(async () => {
  if (req.action === "etat") {
    rep({ outils: Object.keys(modelContext.regs).sort(), journal });
    return;
  }
  if (req.action === "appel") {
    const outil = modelContext.regs[req.tool];
    if (!outil) { rep({ erreur: "outil non enregistré : " + req.tool }); return; }
    const resultat = await outil.execute(req.args || {});
    await new Promise((r) => setTimeout(r, 15));   // laisse les murs se reconstruire
    rep({ resultat, journal, vie: C.joueur.vie, caseOuverte: C.grid[1][0] });
    return;
  }
  if (req.action === "sequence") {
    const resultats = [];
    for (const s of req.steps) {
      const outil = modelContext.regs[s.tool];
      if (!outil) { resultats.push({ ok: false, message: "outil inconnu : " + s.tool }); continue; }
      resultats.push(await outil.execute(s.args || {}));
    }
    await new Promise((r) => setTimeout(r, 15));   // idem
    rep({ resultats, journal, vie: C.joueur.vie, caseOuverte: C.grid[1][0] });
    return;
  }
  rep({ erreur: "action inconnue : " + req.action });
})();