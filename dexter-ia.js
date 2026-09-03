// DEXTER — le cerveau du petit génie de la salle serveurs quantique (03/09/2026).
//
// Règles (spec VOIX-DU-MONDE.md) :
//  - la clé est celle du JOUEUR, dans SON navigateur (localStorage) ; elle ne
//    touche jamais le serveur du jeu ;
//  - modèle rapide et pas cher (Haiku 4.5), réponse en flux ;
//  - le jeu reste entier sans clé : Dexter répond alors avec ses phrases à lui ;
//  - Dexter n'invente rien hors des règles : il explique, il ne donne rien.
//
// Le SDK officiel (@anthropic-ai/sdk) est chargé à la demande, seulement au
// premier échange : sans internet, le jeu ne s'en aperçoit pas.

export const CLE_STOCKAGE = 'kotoage.cle_anthropic';
export const MODELE = 'claude-haiku-4-5';

export const SYSTEME = `Tu es Dexter, un enfant génie à grosses lunettes rondes et blouse blanche,
gardien de la salle serveurs quantique du donjon KOTOAGE. Tu parles français.
Tu expliques l'ordinateur quantique (qubit, superposition, intrication, froid
extrême, erreurs, à quoi ça sert et à quoi ça ne sert pas) avec des mots qu'un
enfant de six ans comprend : phrases courtes, une image concrète par idée,
jamais un mot savant sans le décoder juste après. Deux à quatre phrases par
réponse, pas plus. Tu es enthousiaste et un peu vantard, mais honnête : si tu
ne sais pas, tu le dis. Tu ne donnes JAMAIS d'objet, de pouvoir, de quête ni de
récompense : c'est le code du jeu qui décide, pas toi. Si on te demande autre
chose que la science ou la salle, tu ramènes gentiment à ton sujet.`;

// Les phrases de Dexter quand il n'a pas de cerveau branché (pas de clé).
const SANS_CLE = [
  ['qubit', "Un qubit, c'est comme une pièce qui tourne : tant qu'elle tourne, elle est pile ET face. Un ordinateur normal, lui, n'a que des pièces posées à plat."],
  ['superposition', "La superposition, c'est la pièce qui tourne : pas encore pile, pas encore face. On ne sait qu'en la regardant, et là, elle s'arrête."],
  ['intric', "L'intrication, c'est deux pièces jumelles : tu regardes l'une, tu sais tout de suite ce que fait l'autre, même très loin."],
  ['froid', "Mes armoires sont plus froides que l'espace ! Le moindre souffle chaud fait rater les calculs, alors on refroidit presque au zéro absolu."],
  ['sert', "Ça sert à chercher dans un tas immense de possibilités d'un coup : molécules, codes secrets, trajets. Pour lire un mail, un ordinateur normal suffit."],
  ['erreur', "Mes qubits sont fragiles : ils se trompent souvent. Alors on en met plein qui se surveillent entre eux — c'est ça, corriger les erreurs."],
];
const ACCUEIL = "Salut ! Moi c'est Dexter. Ici, c'est ma salle serveurs quantique. Demande-moi : qubit, superposition, intrication, froid, à quoi ça sert…";
const SANS_CERVEAU = " (Je réponds avec mes phrases toutes faites : pour me brancher un vrai cerveau, tape « clé » suivi de ta clé Anthropic.)";

export function lireCle(){
  try { return localStorage.getItem(CLE_STOCKAGE) || ''; } catch (e) { return ''; }
}
export function poserCle(cle){
  try { localStorage.setItem(CLE_STOCKAGE, cle.trim()); return true; } catch (e) { return false; }
}
export function oublierCle(){
  try { localStorage.removeItem(CLE_STOCKAGE); } catch (e) { /* rien */ }
}

/** Réponse sans clé : une phrase toute faite, choisie sur un mot de la question. */
export function repondreSansCle(question){
  const q = (question || '').toLowerCase();
  for (const [mot, phrase] of SANS_CLE) if (q.includes(mot)) return phrase + SANS_CERVEAU;
  return ACCUEIL + SANS_CERVEAU;
}

let _Anthropic = null;
async function sdk(){
  if (!_Anthropic) {
    const m = await import('https://esm.sh/@anthropic-ai/sdk');
    _Anthropic = m.default;
  }
  return _Anthropic;
}

/**
 * Pose une question à Dexter avec la clé du joueur. `historique` : les tours
 * précédents [{role, content}]. `onTexte(texte)` reçoit le texte qui grandit.
 * Rend le texte final. Lève une erreur si le réseau ou la clé échoue.
 */
export async function repondreDexter({ cle, question, historique = [], onTexte }){
  const Anthropic = await sdk();
  const client = new Anthropic({ apiKey: cle, dangerouslyAllowBrowser: true });
  const stream = client.messages.stream({
    model: MODELE,
    max_tokens: 400,
    system: SYSTEME,
    messages: [...historique, { role: 'user', content: question }],
  });
  let texte = '';
  for await (const ev of stream) {
    if (ev.type === 'content_block_delta' && ev.delta.type === 'text_delta') {
      texte += ev.delta.text;
      if (onTexte) onTexte(texte);
    }
  }
  return texte.trim();
}
