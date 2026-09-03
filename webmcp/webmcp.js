// =====================================================================
//  KOTOAGE / « Le Petit Donjon » — couche WebMCP (hackathon WebMCP 2026)
// ---------------------------------------------------------------------
//  Contrat unique, prouvé par tests/test_webmcp.py :
//
//    creerControleurWebMCP({ modelContext, etat })
//      → enregistre les outils (name, description, inputSchema, execute)
//        sur modelContext.registerTool  (dans le navigateur : le vrai
//        document.modelContext ; en test : un faux enregistré par node).
//
//  Toute la logique des outils est PURE (opère sur `etat`, aucune dépendance
//  WebGL ou DOM) : elle s'exécute donc aussi bien dans Node pour les tests
//  que dans le navigateur.
//  L'intégration au jeu (index.html) est peut-être un "état" branché sur
//  les vraies variables du jeu via des accesseurs (voir webmcp/integration.js) :
//  un Proxy qui traduit les lectures et écritures de `etat` en effets réels
//  (vie → joueur.vie + HUD, grille → grid + reconstruction des murs, etc.).
//  Les champs dernierPi / dernierDefi mémorisent le dernier choix de l'agent
//  pour que l'intégration réelle sache OÙ poser le piège et QUEL défi lancer.
// =====================================================================


// Les cinq etudes que Braignak a deja menees dans le donjon. Ce sont SES
// travaux a lui, sur ce monde-ci : il regarde, il note, il ne touche a rien.
const ETUDES_BRAIGNAK = {
  murs: {
    titre: "Les murs qui s'ouvrent",
    trouvaille: "Un mur ouvert ne se referme jamais tout seul. Sur 40 ouvertures observees, zero refermeture : ce que l'agent ouvre reste ouvert, et le plan de l'etage change pour de bon.",
  },
  gardien: {
    titre: "Le gardien de palier",
    trouvaille: "Le gardien frappe toujours apres un temps d'arret. Ce temps d'arret est sa faiblesse : trois joueurs sur quatre gagnent en attendant ce moment au lieu de foncer.",
  },
  pieges: {
    titre: "Les pieges poses par l'agent",
    trouvaille: "Un piege sert deux fois plus quand il est pose DERRIERE le joueur : les creatures suivent, le joueur non.",
  },
  potions: {
    titre: "Les potions offertes",
    trouvaille: "Une potion donnee a vie pleine ne sert a rien. J'ai compte : une fois sur trois, l'agent soigne quelqu'un qui n'est pas blesse.",
  },
  force: {
    titre: "D'ou vient la force",
    trouvaille: "Aucun joueur n'a gagne un niveau sans combattre. La force ne se recoit pas ici : elle se debloque. C'est la regle de ce monde, et elle tient sur 100 parties.",
  },
};

// LA VIEILLE SORCIERE (SPEC-SORCIERE.md) : sa logique vit dans son propre
// fichier, webmcp/sorciere.js, pour rester pure et testable seule.
const SORCIERE = (typeof require === 'function')
  ? require('./sorciere.js')
  : (typeof window !== 'undefined' ? window.KOTOAGE_SORCIERE : null);

// Grille du donjon (mêmes constantes que index.html) : 28 × 18.
const W = 28;
const H = 18;
const MUR = 0;
const SOL = 1;

// Ingrédients du jeu sur lesquels les outils raisonnent.
const ETAGES = {
  1: "caves",
  2: "ossuaire",
  3: "clairiere",
  4: "voile",
  5: "palier",
};

const LIEUX = {
  village: { nom: "le hameau", piste: "Retrouve l’escalier qui descend, au sud." },
  caves: { nom: "les caves", piste: "Les slimes sont lents : laisse-les venir, puis frappe." },
  ossuaire: { nom: "l’ossuaire", piste: "Les squelettes vacillent : vise et esquive." },
  clairiere: { nom: "la clairière", piste: "Salle ouverte sans murs : surveille les flancs." },
  voile: { nom: "le voile", piste: "Les spectres traversent les murs : garde tes distances." },
  palier: { nom: "le palier", piste: "Le gardien s’éveille : frappe son noyau à mi-vie." },
};

const CHALLENGES = {
  gardien: "Un gardien de palier surgit de l’ombre.",
  guerrier: "Un guerrier te défie dans le couloir.",
  horde: "Une horde surgit des portes.",
};

const POTIONS = { petite: 2, grande: 6 };

// État de jeu REPRÉSENTATIF pour les tests (déterministe — chaque appel
// de test repart de zéro via le harnais). Aucune magie ici : c'est le
// miroir de l'état réel (vie/mana/niveau/grille) que branchera le jeu.
const ETAT_INITIAL = {
  vie: 5,
  vieMax: 10,
  mana: 3,
  manaMax: 10,
  niveau: 1,
  epee: true,
  defisReleves: 0,
  pieges: 0,
  dernierPi: null,    // dernière case piégée (mémorisée pour l'intégration réelle)
  dernierDefi: null,  // dernier type de défi lancé (idem)
  grille: Array.from({ length: H }, (_, y) =>
    Array.from({ length: W }, (_, x) => (x === 0 || y === 0 || x === W - 1 || y === H - 1 ? MUR : SOL)),
  ),
};

// Réponse d'échec normalisée : les agents (et les juges) lisent {ok, message}.
function echec(message) {
  return { ok: false, message };
}

// ---------------------------------------------------------------------
//  Fabrique du contrôleur : enregistre les 7 outils WebMCP.
// ---------------------------------------------------------------------
function creerControleurWebMCP({ modelContext, etat }) {
  if (!modelContext || typeof modelContext.registerTool !== "function") {
    throw new Error("modelContext invalide : registerTool est manquant");
  }

  const outils = [
    {
      name: "etat_joueur",
      description:
        "Renvoie une vue structurée de l’état du joueur (vie, mana, étage, équipement, compteurs).",
      inputSchema: { type: "object", properties: {}, required: [] },
      execute: async () => ({
        ok: true,
        vie: etat.vie,
        vieMax: etat.vieMax,
        mana: etat.mana,
        manaMax: etat.manaMax,
        niveau: etat.niveau,
        epee: etat.epee,
        defisReleves: etat.defisReleves,
      }),
    },

    {
      name: "donner_potion",
      description:
        "Accorde une potion au joueur : petite = +2 vie, grande = +6. La vie est plafonnée à la vie max.",
      inputSchema: {
        type: "object",
        properties: { type: { type: "string", enum: ["petite", "grande"] } },
        required: ["type"],
      },
      execute: async ({ type }) => {
        const gain = POTIONS[type];
        if (!gain) return echec("type de potion inconnu : " + type);
        const avant = etat.vie;
        etat.vie = Math.min(etat.vieMax, etat.vie + gain);
        return { ok: true, avant, apres: etat.vie, message: "Vie " + avant + " → " + etat.vie };
      },
    },

    {
      name: "ouvrir_mur",
      description:
        "Ouvre un mur aux coordonnées (x, z) de la grille 28×18. Refusé hors grille, sur du sol, ou si déjà ouvert.",
      inputSchema: {
        type: "object",
        properties: {
          x: { type: "integer", minimum: 0, maximum: W - 1 },
          z: { type: "integer", minimum: 0, maximum: H - 1 },
        },
        required: ["x", "z"],
      },
      execute: async ({ x, z }) => {
        const cx = Math.round(Number(x));
        const cz = Math.round(Number(z));
        if (!Number.isInteger(cx) || !Number.isInteger(cz) || cx < 0 || cx > W - 1 || cz < 0 || cz > H - 1) {
          return echec("coordonnées hors de la grille " + W + "×" + H + " : (" + x + ", " + z + ")");
        }
        if (etat.grille[cz][cx] !== MUR) {
          return echec("case (" + cx + ", " + cz + ") n’est pas un mur : rien à ouvrir");
        }
        etat.grille[cz][cx] = SOL;
        return { ok: true, x: cx, z: cz, message: "Mur ouvert à (" + cx + ", " + cz + ")." };
      },
    },

    {
      name: "placer_piege",
      description: "Pose un piège sur une case sol (x, z). Refusé sur un mur ou hors grille.",
      inputSchema: {
        type: "object",
        properties: {
          x: { type: "integer", minimum: 0, maximum: W - 1 },
          z: { type: "integer", minimum: 0, maximum: H - 1 },
        },
        required: ["x", "z"],
      },
      execute: async ({ x, z }) => {
        const cx = Math.round(Number(x));
        const cz = Math.round(Number(z));
        if (!Number.isInteger(cx) || !Number.isInteger(cz) || cx < 0 || cx > W - 1 || cz < 0 || cz > H - 1) {
          return echec("coordonnées hors de la grille " + W + "×" + H + " : (" + x + ", " + z + ")");
        }
        if (etat.grille[cz][cx] !== SOL) {
          return echec("on ne piège que sur du sol — (" + cx + ", " + cz + ") est un mur");
        }
        etat.dernierPi = { x: cx, z: cz };
        etat.pieges += 1;
        return { ok: true, x: cx, z: cz, message: "Piège posé à (" + cx + ", " + cz + "). Total : " + etat.pieges };
      },
    },

    {
      name: "inspirer",
      description: "Donne une piste contextuelle pour un lieu (village ou étage du donjon).",
      inputSchema: {
        type: "object",
        properties: { lieu: { type: "string", enum: Object.keys(LIEUX) } },
        required: ["lieu"],
      },
      execute: async ({ lieu }) => {
        const lieuConnu = LIEUX[lieu];
        if (!lieuConnu) return echec("lieu inconnu : " + lieu);
        return { ok: true, lieu, message: lieuConnu.piste };
      },
    },

    {
      name: "defier",
      description: "Fait surgir un défi : gardien, guerrier ou horde. Comptabilise le défi relevé.",
      inputSchema: {
        type: "object",
        properties: { type: { type: "string", enum: Object.keys(CHALLENGES) } },
        required: ["type"],
      },
      execute: async ({ type }) => {
        const annonce = CHALLENGES[type];
        if (!annonce) return echec("défi inconnu : " + type);
        etat.dernierDefi = type;
        etat.defisReleves += 1;
        return { ok: true, type, message: annonce, defisReleves: etat.defisReleves };
      },
    },

    {
      name: "raconter",
      description: "Narration courte d’un étage (1 à 5 ; 0 = le village).",
      inputSchema: {
        type: "object",
        properties: { etage: { type: "integer", minimum: 0, maximum: 5 } },
        required: ["etage"],
      },
      execute: async ({ etage }) => {
        const n = Number(etage);
        if (!Number.isInteger(n) || n < 0 || n > 5) {
          return echec("étage invalide : " + etage);
        }
        if (n === 0) {
          return { ok: true, etage: n, message: "Le hameau dort sous un ciel photographié." };
        }
        const cle = ETAGES[n];
        return {
          ok: true,
          etage: n,
          message: "Étage " + n + " — " + LIEUX[cle].nom + ". " + LIEUX[cle].piste,
        };
      },
    },
    {
      name: "braignak_etude",
      description:
        "Interroge Braignak, le veilleur du donjon : il rend une de ses cinq etudes deja menees, ou il en prend une nouvelle sur le sujet demande. Sans sujet, il liste ses etudes.",
      inputSchema: {
        type: "object",
        properties: {
          sujet: {
            type: "string",
            description:
              "Le sujet a etudier. Un des cinq deja etudies (murs, gardien, pieges, potions, force) rend la trouvaille tout de suite ; tout autre sujet lance une nouvelle etude.",
          },
        },
      },
      execute: async ({ sujet } = {}) => {
        const liste = Object.keys(ETUDES_BRAIGNAK).map(
          (c) => c + " — " + ETUDES_BRAIGNAK[c].titre
        );
        if (!sujet) {
          return {
            ok: true,
            etudes: liste,
            message: "Braignak a mene cinq etudes : " + liste.join(" · "),
          };
        }
        const cle = String(sujet).trim().toLowerCase();
        const connue = ETUDES_BRAIGNAK[cle];
        if (connue) {
          etat.derniereEtude = { sujet: cle, nouvelle: false };
          return {
            ok: true,
            sujet: cle,
            titre: connue.titre,
            nouvelle: false,
            message: connue.titre + " : " + connue.trouvaille,
          };
        }
        etat.derniereEtude = { sujet: String(sujet).slice(0, 80), nouvelle: true };
        return {
          ok: true,
          sujet: String(sujet).slice(0, 80),
          nouvelle: true,
          message:
            "Braignak prend une nouvelle etude : « " +
            String(sujet).slice(0, 80) +
            " ». Il s'ecarte, il observe, il revient te dire ce qu'il a vu.",
        };
      },
    },
    {
      name: "marchander",
      description:
        "Marchande avec la Vieille Sorciere, qui vend des armes au fond du donjon. Sans argument : ce qu'elle vend. Avec {arme} : son prix. Avec {arme, offre} : sa reponse. Elle ne descend jamais sous 90 % de son prix, et marchander trop bas la vexe (le prix monte) — trois fois et elle s'embrouille.",
      inputSchema: {
        type: "object",
        properties: {
          arme: { type: "string", description: "dague, epee, hache ou baton" },
          offre: { type: "integer", minimum: 0, description: "ce que le joueur propose" },
        },
      },
      execute: async ({ arme, offre } = {}) => {
        if (!SORCIERE) return echec("la sorciere n'est pas la");
        if (!etat.sorciere) etat.sorciere = SORCIERE.creerSorciere();
        const demande = {};
        if (arme !== undefined) demande.arme = arme;
        if (offre !== undefined) demande.offre = offre;
        return SORCIERE.marchander(etat.sorciere, demande);
      },
    },
  ];

  for (const outil of outils) {
    modelContext.registerTool(outil);
  }
  return outils;
}

const API = { creerControleurWebMCP, ETAT_INITIAL, W, H, MUR, SOL, LIEUX, CHALLENGES, POTIONS, ETAGES, ETUDES_BRAIGNAK, SORCIERE };

// Compatibilité double rôle :
//  · Node  (tests) : require('webmcp/webmcp.js') → module.exports.
//  · Navigateur  (index.html) : <script> classique → window.KOTOAGE_WEBMCP.
if (typeof module !== "undefined" && module.exports) module.exports = API;
if (typeof window !== "undefined") window.KOTOAGE_WEBMCP = API;