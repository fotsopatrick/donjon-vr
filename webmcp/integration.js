// =====================================================================
//  webmcp/integration.js — pont RÉEL entre la couche WebMCP (webmcp.js)
//  et l'état du jeu (module principal de index.html).
// ---------------------------------------------------------------------
//  Chargé comme <script type="module"> APRÈS le module du jeu. Il lit :
//    · window.KOTOAGE_WEBMCP        (couche pure, chargée en classique)
//    · window.__webmcpConnexion     (pont exposé par le module du jeu)
//    · document.modelContext        (l'API WebMCP réelle du navigateur)
//  puis enregistre les 8 outils. Les effets de bord réels sont déclenchés
//  par des accesseurs/proxy sur `etat` :
//    · vie   → joueur.vie + HUD (dessinerCoeurs)
//    · grille → vraie grille du jeu (grid), murs reconstruits
//    · pieges → poserPiege sur la case mémorisée (dernierPi)
//    · defisReleves → spawn de créatures réelles près du joueur
//
//  Sans document.modelContext (navigateur sans WebMCP) : ne fait RIEN.
//  Le jeu reste intact. Aucune dépendance ajoutée au rendu.
// =====================================================================
(() => {
  const M = typeof window !== "undefined" && window.KOTOAGE_WEBMCP;
  const C = typeof window !== "undefined" && window.__webmcpConnexion;
  const ctx =
    (typeof document !== "undefined" && document.modelContext) ||
    (typeof globalThis !== "undefined" && globalThis.__modelContextFake);
  if (!M || !C || !ctx || typeof ctx.registerTool !== "function") return;

  // Derniers choix de l'agent, mémorisés par la couche pure (webmcp.js).
  let dernierPi = null;
  let dernierDefi = null;

  // Vue proxy bidirectionnelle sur la vraie grille du jeu (grid[y][x]).
  // Les lectures tombent dans le vrai tableau ; une écriture (ouvrir_mur)
  // modifie la grille PUIS reconstruit les murs en 3D.
  function grilleReelle() {
    const G = C.grid;
    return new Proxy(G, {
      get(emploi, cle) {
        const iy = Number(cle);
        const ligne = emploi[cle];
        if (Array.isArray(ligne)) {
          return new Proxy(ligne, {
            set(l2, c, v) {
              l2[c] = v;
              if (Number.isInteger(iy) && Number.isInteger(+c)) propager(iy, +c);
              return true;
            },
          });
        }
        return ligne;
      },
    });
  }

  let _timerMurs = null;
  function propager(y, x) {
    // Retire la torche qui pendait sur la case ouverte (donnée, pas le mesh).
    try {
      if (C.torches) C.torches = C.torches.filter((t) => !(t.x === x && t.y === y));
    } catch (e) {}
    // Reconstruit la pierre une seule fois par rafale.
    if (_timerMurs) return;
    _timerMurs = setTimeout(() => {
      _timerMurs = null;
      try { C.construireMurs(); } catch (e) {}
    }, 0);
  }

  const etatReel = {
    get vie() { return C.joueur.vie; },
    set vie(v) { C.joueur.vie = v; try { C.dessinerCoeurs(); } catch (e) {} },
    get vieMax() { return C.joueur.vieMax; },
    set vieMax(v) { C.joueur.vieMax = v; },
    get mana() { return C.joueur.mana; },
    set mana(v) { C.joueur.mana = v; },
    get manaMax() { return C.joueur.manaMax; },
    get niveau() { return C.niveau; },
    get epee() { return !!C.joueur.epee; },
    _defis: 0,
    _pieges: 0,
    get defisReleves() { return this._defis; },
    set defisReleves(v) { this._defis = v; lancerDefi(); },
    get pieges() { return this._pieges; },
    set pieges(v) { this._pieges = v; if (dernierPi) C.poserPiege(dernierPi.x, dernierPi.z); },
    get dernierPi() { return dernierPi; },
    set dernierPi(v) { dernierPi = v; },
    get dernierDefi() { return dernierDefi; },
    set dernierDefi(v) { dernierDefi = v; },
    _etude: null,
    get derniereEtude() { return this._etude; },
    // Braignak prend une nouvelle etude : le jeu le fait s'ecarter, reflechir,
    // puis revenir donner sa trouvaille une seule fois.
    set derniereEtude(v) {
      this._etude = v;
      try { if (typeof C.braignakEtudier === "function") C.braignakEtudier(v); } catch (e) {}
    },
    get grille() { return grilleReelle(); },
  };

  // defier : fait surgir de vraies créatures près du joueur (via D.inspecterCreature).
  function lancerDefi() {
    const types = {
      gardien: ["slime_rouge", "slime_rouge"],
      guerrier: ["paysan", "squelette"],
      horde: ["rat", "rat", "slime"],
    };
    const liste = types[dernierDefi] || types.guerrier;
    const T = C.T || 2.6;
    const x = C.joueur.x + 1.5;
    const z = C.joueur.z - 3;
    liste.forEach((type, i) => {
      try { C.monte(type, x + i * 1.8, z); } catch (e) {}
    });
  }

  let outils;
  try {
    outils = M.creerControleurWebMCP({ modelContext: ctx, etat: etatReel });
  } catch (e) {
    return;
  }

  // Chaque RÉUSSITE de l'agent apparaît dans le HUD du jeu (dire) : le
  // joueur voit ce que son co-maître de jeu vient de faire. Les refus
  // restent silencieux (message destiné à l'agent, pas au joueur).
  for (const o of outils) {
    const base = o.execute;
    o.execute = async (args) => {
      const r = await base(args);
      try { if (r && r.ok && r.message && typeof C.dire === "function") C.dire(r.message); } catch (e) {}
      return r;
    };
  }

  try { window.__webmcpActif = true; } catch (e) {}
})();