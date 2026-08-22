/* chat-traduction.js — TranslationService du chat (feature 22/08).

   Le français s'affiche TOUJOURS immédiatement, la traduction japonaise arrive
   en arrière-plan. Cache par (source|target|texte) : on ne traduit jamais deux
   fois la même phrase. Aucune clé dans le navigateur : le serveur local
   (chat-traduction.py, port 8766) possède DEEPSEEK_API_KEY, ou répond 501.
   Si le serveur est absent/lent/en erreur, un petit dictionnaire de phrases
   courantes sert de secours honnête ; sinon on garde le français, sans casser
   le chat. Le module n'importe RIEN du jeu ni du world builder : le chat et
   le monde 3D restent deux responsabilités séparées.
*/
const URL_TRADUCTION = 'http://127.0.0.1:8766/traduire';
const DELAI_MAX_MS = 4000;

/* ── secours hors-ligne : quelques phrases courantes, japonais naturel ── */
const DICTIONNAIRE_FR_JA = {
  'bonjour': 'こんにちは。',
  'salut': 'やあ。',
  'bonsoir': 'こんばんは。',
  'bonne nuit': 'おやすみ。',
  'au revoir': 'さようなら。',
  'merci': 'ありがとう。',
  'merci beaucoup': 'ありがとうございます。',
  'de rien': 'どういたしまして。',
  'bonne chance': 'がんばってね。',
  'bon appétit': 'いただきます。',
  'comment tu vas': '元気？',
  'comment vas tu': '元気？',
  'ça va': '大丈夫。',
  'ça va je vais rentrer chez moi': '大丈夫。家に帰るよ。',
  'je vais bien': '元気だよ。',
  'je suis perdu': '道に迷った。',
  'je suis fatigue': '疲れた。',
  'j ai faim': 'お腹が空いた。',
  'aide moi': '助けて。',
  'a l aide': '助けて！',
  'attention': '気をつけて。',
  'bonjour vous allez bien': 'こんにちは、お元気ですか？',
  'bonjour bienvenue dans mon monde': 'こんにちは！私の世界へようこそ。',
  'cette maison est magnifique': 'この家は本当に美しいね。',
  'attends moi ici je reviens bientôt': 'ここで待っていて。すぐ戻るから。',
  'attends moi ici je reviens bientot': 'ここで待っていて。すぐ戻るから。',
  'je m appelle': null,   // géré par le modèle ci-dessous
  'je m appelle patrick': '私の名前はパトリックです。',
  'comment tu t appelles': '君の名前は何？',
  'je t aime': '好きだよ。',
  'tu es fort': '君は強いね。',
  'c est beau': 'きれいだね。',
  'c est magnifique': 'すごくきれいだね。',
  'bienvenue': 'ようこそ。',
  'ou est la sortie': '出口はどこ？',
  'par ici': 'こっちだよ。',
  'merci de m aider': '助けてくれてありがとう。',
  'cet endroit est magnifique': 'この場所は本当に美しいね。',
};

function normaliserFR(t) {
  return (t || '').toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')   // enlève les accents
    .replace(/[.,!?;:«»"'()…]/g, ' ')                    // ponctuation → espace
    .replace(/\s+/g, ' ').trim();
}

const Traduction = {
  _cache: new Map(),
  _appelsServeur: 0,
  _delaiMaxMs: DELAI_MAX_MS,

  /* translate(text, source, target) — l'interface conceptuelle demandée.
     Ne renvoie JAMAIS d'exception : null = pas de traduction (français gardé). */
  async translate(text, source = 'fr', target = 'ja') {
    const t = (text || '').trim();
    if (!t) return null;                       // 3. message vide
    const cle = source + '|' + target + '|' + t;
    if (this._cache.has(cle)) return this._cache.get(cle);   // 8. cache

    let resultat = null;
    try {
      resultat = await this._servirAvecDelai(t, source, target);
    } catch (e) { resultat = null; }           // 6/7. erreur ou timeout
    if (!resultat) resultat = this._dictionnaire(t) || null;
    if (resultat) this._cache.set(cle, resultat);
    return resultat;
  },

  async _servirAvecDelai(texte, source, target) {
    this._appelsServeur++;
    const promesse = this._serveur(texte, source, target);
    const sablier = new Promise((_, rej) =>
      setTimeout(() => rej(new Error('timeout traduction')), this._delaiMaxMs));
    return Promise.race([promesse, sablier]);
  },

  async _serveur(texte, source, target) {
    const rep = await fetch(URL_TRADUCTION, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: texte, source, target }),
    });
    if (!rep.ok) return null;
    const d = await rep.json();
    const tr = d && d.traduction;
    return (typeof tr === 'string' && tr.trim()) ? tr.trim() : null;
  },

  _dictionnaire(texte) {
    const n = normaliserFR(texte);
    if (!n) return null;
    if (DICTIONNAIRE_FR_JA[n]) return DICTIONNAIRE_FR_JA[n];
    // une phrase qui CONTIENT un élément connu (ex. « Je m'appelle Lucie. »)
    if (/^je m appelle /.test(n)) {
      const nom = n.replace(/^je m appelle /, '').trim();
      return '私の名前は' + nom + 'です。';
    }
    return null;   // inconnu → le français est conservé (noms propres intacts)
  },

  purgerCache() { this._cache.clear(); },
  get appelsServeur() { return this._appelsServeur; },
};

window.Traduction = Traduction;
