// Test du garde-fou anti-répétition — écrit AVANT le code, sur ordre de Patrick.
// Ce qu'on vérifie :
//   1. Il REPÈRE une consigne déjà acquise que Patrick redit (« écris les tests »,
//      « demande-moi point par point », « ressors les phrases citées »).
//   2. Il RÉPOND une note douce : « déjà acquis, tu peux économiser ça ».
//   3. Il NE se déclenche PAS sur une demande normale (pas de faux positif gênant).
//   4. Une règle oubliée (retirée) ne se déclenche plus.

const { verifier, REGLES, oublier } = require('./garde-repetitions.js');

let ok = 0, ko = 0;
function v(nom, cond) {
  if (cond) { ok++; console.log('  ✓ ' + nom); }
  else { ko++; console.log('  ✗ ' + nom); }
}

// 1 & 2 — il repère et il répond
v('repère « écris les tests avant »',
  verifier('et écris les tests avant de câbler')?.regle === 'tests-avant');
v('repère « demande-moi point par point »',
  verifier('demande-moi point par point ce que je choisis')?.regle === 'point-par-point');
v('repère « ressors les phrases citées »',
  verifier('quand tu dis ça, ressors les phrases en question')?.regle === 'resurfacer');
v('la note est douce et nomme la règle',
  /déjà acquis/i.test(verifier('écris les tests')?.note || ''));

// 3 — pas de faux positif sur une vraie demande de travail
v('ne se déclenche PAS sur « code le bracelet de résurrection »',
  verifier('code le bracelet de résurrection') === null);
v('ne se déclenche PAS sur « ajoute un boss à l’étage 3 »',
  verifier('ajoute un boss à l’étage 3') === null);

// 4 — on peut retirer une règle (elle ne mord plus)
oublier('tests-avant');
v('« écris les tests » ne se déclenche plus après oubli',
  verifier('écris les tests') === null);

console.log(`\n${ok} réussis, ${ko} échoués`);
process.exit(ko === 0 ? 0 : 1);
