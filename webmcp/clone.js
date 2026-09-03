// =====================================================================
//  webmcp/clone.js — LE CLONE et sa compétence unique BONNE ÉTOILE.
// ---------------------------------------------------------------------
//  Contrat : SPEC-SORCIERE.md. Preuves : tests/test_bonne_etoile.py.
//
//  Bonne Étoile ne s'achète pas : le Clone l'a, les autres ne l'ont pas.
//  La PREMIÈRE fois qu'un coup devrait le tuer dans une partie, il survit
//  avec 1 point de vie. Une seule fois. Ensuite il meurt comme tout le
//  monde.
//
//  Logique PURE : aucun hasard, aucune horloge. Mêmes dégâts, même
//  résultat, toujours — c'est ce qui la rend testable.
// =====================================================================

const MESSAGE = 'Bonne Étoile — tu devais mourir. Pas aujourd’hui.';

function estClone(joueur) {
  return String(joueur || '').trim().toLowerCase() === 'clone';
}

function creerPorteur(joueur, vie) {
  const clone = estClone(joueur);
  return {
    joueur: String(joueur || ''),
    clone,
    vie: Number(vie),
    // seul le Clone part avec l'étoile en réserve
    bonneEtoile: clone,
  };
}

function encaisser(porteur, degats) {
  const d = Math.max(0, Number(degats) || 0);
  const restant = porteur.vie - d;

  // 1. le coup ne tue pas : rien d'autre à dire, l'étoile reste en réserve
  if (restant > 0) {
    porteur.vie = restant;
    return {
      vie: porteur.vie, mort: false, declenchee: false,
      disponible: porteur.bonneEtoile, message: '',
    };
  }

  // 2. le coup tue, et l'étoile est là : il survit à 1, et elle est usée
  if (porteur.bonneEtoile) {
    porteur.bonneEtoile = false;
    porteur.vie = 1;
    return {
      vie: 1, mort: false, declenchee: true,
      disponible: false, message: MESSAGE,
    };
  }

  // 3. le coup tue, et il n'y a plus d'étoile
  porteur.vie = 0;
  return {
    vie: 0, mort: true, declenchee: false,
    disponible: false, message: '',
  };
}

// Nom UNIQUE : les trois fichiers sont charges en <script> classique, ils
// partagent donc le meme espace de noms. Deux « const API » = page morte.
const API_CLONE = { creerPorteur, encaisser, estClone, MESSAGE };

if (typeof module !== 'undefined' && module.exports) module.exports = API_CLONE;
if (typeof window !== 'undefined') window.KOTOAGE_CLONE = API_CLONE;
