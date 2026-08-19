// GARDE-FOU ANTI-RÉPÉTITION — pour Patrick, pas pour l'agent.
//
// Il surveille les consignes que Patrick a DÉJÀ posées comme règles durables.
// Quand il en redit une, le garde-fou le signale doucement : « c'est acquis,
// tu peux économiser ça » — pour lui libérer le cerveau (sa demande, 19/08).
//
// Il ne bloque rien, il n'agit pas à sa place : il informe, une fois, gentiment.
// Chaque règle a un déclencheur (regex) et une formulation courte.

const sansAccent = s => (s || '').toLowerCase()
  .normalize('NFD').replace(/[̀-ͯ]/g, '');

// Les règles ACQUISES — ce que Patrick n'a plus besoin de répéter.
let REGLES = [
  {
    id: 'tests-avant',
    libelle: 'écrire les tests d’abord',
    // « écris les tests », « les tests avant », « test d'abord »
    detecte: t => /(ecri|ecris|met).*(les )?tests?|tests? (avant|d.abord)|les tests d.abord/.test(t),
  },
  {
    id: 'point-par-point',
    libelle: 'demander point par point (ne pas laisser de travail dormant)',
    detecte: t => /point par point|travail dormant|demande.*(ce que je choisi|mon choix)/.test(t),
  },
  {
    id: 'resurfacer',
    libelle: 're-citer le contenu référencé au lieu de le désigner de loin',
    detecte: t => /ressor|re.?cite|remet.*(sous.*yeux|les phrases)|redonne.*(phrase|option)|les phrases en question/.test(t),
  },
];

// Renvoie { regle, libelle, note } si Patrick redit une règle acquise, sinon null.
function verifier(message) {
  const t = sansAccent(message);
  for (const r of REGLES) {
    if (r.detecte(t)) {
      return {
        regle: r.id,
        libelle: r.libelle,
        note: `💡 Déjà acquis : « ${r.libelle} ». Tu n’as plus besoin de le préciser — `
            + `je l’applique par défaut. (« oublie la règle ${r.id} » pour la retirer.)`,
      };
    }
  }
  return null;
}

// Retirer une règle devenue fausse ou gênante.
function oublier(id) {
  const avant = REGLES.length;
  REGLES = REGLES.filter(r => r.id !== id);
  return REGLES.length < avant;
}

// Ajouter une règle acquise (quand une nouvelle consigne durable apparaît).
function ajouter(id, libelle, detecte) {
  if (!REGLES.some(r => r.id === id)) REGLES.push({ id, libelle, detecte });
}

module.exports = { verifier, oublier, ajouter, REGLES };
