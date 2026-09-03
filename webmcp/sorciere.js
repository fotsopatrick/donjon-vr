// =====================================================================
//  webmcp/sorciere.js — LA VIEILLE SORCIÈRE, marchande d'armes.
// ---------------------------------------------------------------------
//  Contrat écrit dans SPEC-SORCIERE.md, prouvé par tests/test_sorciere.py.
//
//  Elle vend cher, elle ne descend jamais sous son prix plancher (90 % du
//  prix demandé), et marchander l'agace : chaque offre trop basse lui coûte
//  une patience ET fait MONTER son prix de 10 %. À patience zéro, elle
//  s'embrouille et ne vend plus rien de la conversation.
//
//  Logique PURE : aucune horloge, aucun hasard, aucun DOM, aucun réseau.
//  Même offre, même réponse, toujours — comme un garde-fou.
// =====================================================================

const ARMES = {
  dague: { nom: 'dague', titre: 'Dague ébréchée', prix: 30 },
  epee: { nom: 'epee', titre: 'Épée courte', prix: 90 },
  hache: { nom: 'hache', titre: 'Hache de guerre', prix: 180 },
  baton: { nom: 'baton', titre: 'Bâton de sorcière', prix: 250 },
};

const PATIENCE_DEPART = 3;
const PART_PLANCHER = 0.9;     // elle ne descend jamais sous 90 % du prix

// LE CLONE : le seul avec qui elle ne s'embrouille pas (SPEC-SORCIERE.md).
// Elle lui laisse deux fois plus de patience, un plancher plus bas, et une
// offre insultante ne fait PAS monter son prix. Elle ne descend pas non plus
// sous SON plancher a lui : c'est un ami, pas une bonne affaire.
const CLONE = { patience: 6, plancher: 0.75, prixMonte: false };
// Une offre insultante fait monter le prix de 10 %. On calcule en dixièmes
// ENTIERS (x 11 / 10) : avec 90 * 1.1 la machine rend 99.000000000000014, que
// l'arrondi vers le haut transforme en 100. Un prix faux d'une piece a cause
// d'une virgule flottante, c'est exactement le genre de bug qu'un test attrape
// et qu'un oeil ne voit pas.
const HAUSSE_NUM = 11;
const HAUSSE_DEN = 10;

const MOTS = {
  contente: 'Enfin quelqu’un qui sait compter.',
  ralant: 'Tu me voles, mais prends-la. Ne reviens pas me pleurer.',
  refus: 'Ce n’est pas un prix, c’est une insulte.',
  embrouille: 'Dehors. Reviens quand tu auras appris.',
  vide: 'Je n’ai plus rien pour toi.',
  inconnue: 'Je ne vends pas ça. Regarde ce que j’ai.',
};

// Avec le Clone, elle n'a pas la meme voix.
const MOTS_CLONE = {
  contente: 'Toi, tu sais ce que valent les choses.',
  ralant: 'Pour toi, et pour personne d’autre.',
  refus: 'Même à toi, non. Remonte ton offre.',
  embrouille: 'Va prendre l’air. On reparlera.',
  vide: 'Je n’ai plus rien pour toi.',
  inconnue: 'Je ne vends pas ça. Regarde ce que j’ai.',
};

function mots(sorciere) { return sorciere.clone ? MOTS_CLONE : MOTS; }

function creerSorciere(joueur) {
  const clone = String(joueur || '').trim().toLowerCase() === 'clone';
  const prix = {};
  for (const c of Object.keys(ARMES)) prix[c] = ARMES[c].prix;
  return { patience: clone ? CLONE.patience : PATIENCE_DEPART, prix, vendues: [], clone };
}

function plancher(sorciere, cle) {
  // Le plancher suit le prix DE DÉPART, pas le prix monté : sinon marchander
  // bas ferait monter le plancher, et le joueur ne pourrait plus jamais payer.
  const part = sorciere.clone ? CLONE.plancher : PART_PLANCHER;
  return Math.ceil(ARMES[cle].prix * part);
}

function catalogue(sorciere) {
  return Object.keys(ARMES)
    .filter((c) => !sorciere.vendues.includes(c))
    .map((c) => ({ nom: c, titre: ARMES[c].titre, prix: sorciere.prix[c], plancher: plancher(sorciere, c) }));
}

function reponse(sorciere, extra) {
  return Object.assign({ ok: true, vendu: false, patience: sorciere.patience }, extra);
}

function marchander(sorciere, demande) {
  const d = demande || {};

  // 1. plus rien à vendre du tout
  const restantes = catalogue(sorciere);
  if (!d.arme && restantes.length === 0) {
    return reponse(sorciere, { armes: [], message: mots(sorciere).vide });
  }

  // 2. sans arme : elle montre ce qu'elle a
  if (!d.arme) {
    return reponse(sorciere, { armes: restantes, message: 'Voilà ce que j’ai. Les prix sont les prix.' });
  }

  const cle = String(d.arme).trim().toLowerCase();
  if (!ARMES[cle]) {
    return { ok: false, vendu: false, patience: sorciere.patience, message: mots(sorciere).inconnue };
  }

  // 3. déjà vendue : elle ne la revend pas
  if (sorciere.vendues.includes(cle)) {
    return reponse(sorciere, { arme: cle, message: mots(sorciere).vide });
  }

  const prix = sorciere.prix[cle];

  // 4. sans offre : elle annonce son prix
  if (d.offre === undefined || d.offre === null) {
    return reponse(sorciere, { arme: cle, prix, message: ARMES[cle].titre + ' : ' + prix + '. C’est le prix.' });
  }

  // 5. embrouillée : elle ne vend plus rien, même très cher
  if (sorciere.patience <= 0) {
    return reponse(sorciere, { arme: cle, prix, message: mots(sorciere).embrouille });
  }

  const offre = Number(d.offre);
  const bas = plancher(sorciere, cle);

  // 6. offre au prix ou au-dessus : elle vend, contente
  if (offre >= prix) {
    sorciere.vendues.push(cle);
    return reponse(sorciere, { arme: cle, prix, vendu: true, paye: offre, message: mots(sorciere).contente });
  }

  // 7. offre entre le plancher et le prix : elle vend en râlant, -1 patience
  if (offre >= bas) {
    sorciere.patience -= 1;
    sorciere.vendues.push(cle);
    return reponse(sorciere, { arme: cle, prix, vendu: true, paye: offre, message: mots(sorciere).ralant });
  }

  // 8. offre sous le plancher : refus, -1 patience, et le prix MONTE
  sorciere.patience -= 1;
  // Avec le Clone, elle ne punit pas : le prix ne bouge pas.
  if (!sorciere.clone) sorciere.prix[cle] = Math.ceil((prix * HAUSSE_NUM) / HAUSSE_DEN);
  const finale = sorciere.patience <= 0 ? mots(sorciere).embrouille : mots(sorciere).refus;
  return reponse(sorciere, { arme: cle, prix: sorciere.prix[cle], message: finale });
}

// Nom UNIQUE : les trois fichiers sont charges en <script> classique, ils
// partagent donc le meme espace de noms. Deux « const API » = page morte.
const API_SORCIERE = { creerSorciere, marchander, catalogue, ARMES, PATIENCE_DEPART, CLONE };

if (typeof module !== 'undefined' && module.exports) module.exports = API_SORCIERE;
if (typeof window !== 'undefined') window.KOTOAGE_SORCIERE = API_SORCIERE;
