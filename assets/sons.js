/* ═══════════════════════════════════════════════════════════════════
   SONS DU JEU — tout fabriqué par le navigateur, zéro fichier

   Pourquoi aucun fichier : un .wav de coup d'épée pèse 30 à 80 ko, il
   faut le télécharger, le décoder, et il arrive en retard le premier
   coup. Ici, chaque bruit est calculé au moment où il sort. Poids
   ajouté au jeu : ce fichier, environ 6 ko. Latence : nulle.

   Comment s'en servir :
       <script src="sons.js"></script>
       Sons.demarrer();          // une fois, sur le premier clic
       Sons.coup();              // le joueur donne un coup
       Sons.impact();            // le coup touche
       Sons.degat();             // le joueur prend un coup
       Sons.pas();               // un pas
       Sons.ramasse();           // objet ramassé
       Sons.porte();             // porte / escalier
       Sons.mort();
       Sons.volume(0.5);         // 0 = muet, 1 = fort

   Un navigateur refuse de jouer un son tant que la personne n'a pas
   cliqué. D'où `demarrer()`, à appeler au premier clic ou à la
   première touche.
   ═══════════════════════════════════════════════════════════════════ */

const Sons = (() => {
  let ctx = null;
  let maitre = null;
  let reverb = null, envoi = null;     // la salle de pierre : chaque son y laisse une traînée
  let volumeVoulu = 0.35;

  // Une impulsion de réverbération fabriquée : du bruit qui décroît.
  // C'est ce qui donne « on est dans un donjon » plutôt que « bip de console ».
  function faireReverb() {
    const dur = 1.7, n = Math.floor(ctx.sampleRate * dur);
    const buf = ctx.createBuffer(2, n, ctx.sampleRate);
    for (let c = 0; c < 2; c++) {
      const d = buf.getChannelData(c);
      for (let i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / n, 2.6);
    }
    reverb = ctx.createConvolver(); reverb.buffer = buf;
    const graveReverb = ctx.createBiquadFilter();   // une réverb sombre, pas brillante
    graveReverb.type = 'lowpass'; graveReverb.frequency.value = 2200;
    envoi = ctx.createGain(); envoi.gain.value = 0.34;
    envoi.connect(reverb); reverb.connect(graveReverb); graveReverb.connect(maitre);
  }

  function demarrer() {
    if (ctx) { if (ctx.state === 'suspended') ctx.resume(); return; }
    try {
      ctx = new (window.AudioContext || window.webkitAudioContext)();
      maitre = ctx.createGain();
      maitre.gain.value = volumeVoulu;
      maitre.connect(ctx.destination);
      faireReverb();
    } catch (e) { ctx = null; }
  }

  function volume(v) {
    volumeVoulu = Math.max(0, Math.min(1, v));
    if (maitre) maitre.gain.value = volumeVoulu;
  }

  /* Une note : une forme d'onde dont la hauteur glisse de f1 vers f2,
     et dont le volume s'éteint tout seul. C'est la brique de tout. */
  function note({ f1, f2 = f1, duree = 0.12, forme = 'square', vol = 0.5, retard = 0, glisse = 'exp' }) {
    if (!ctx) return;
    const t = ctx.currentTime + retard;
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = forme;
    o.frequency.setValueAtTime(f1, t);
    if (f2 !== f1) {
      if (glisse === 'exp') o.frequency.exponentialRampToValueAtTime(Math.max(1, f2), t + duree);
      else o.frequency.linearRampToValueAtTime(f2, t + duree);
    }
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(vol, t + 0.005);   // attaque très courte
    g.gain.exponentialRampToValueAtTime(0.0001, t + duree);
    o.connect(g); g.connect(maitre); if (envoi) g.connect(envoi);   // + la traînée de salle
    o.start(t); o.stop(t + duree + 0.02);
  }

  /* Du souffle : du bruit blanc filtré. C'est ce qui fait la
     différence entre un « bip » de console et un vrai choc. */
  function souffle({ duree = 0.12, coupure = 1200, type = 'lowpass', vol = 0.5, retard = 0, chute = 0 }) {
    if (!ctx) return;
    const t = ctx.currentTime + retard;
    const n = Math.max(1, Math.floor(ctx.sampleRate * duree));
    const tampon = ctx.createBuffer(1, n, ctx.sampleRate);
    const d = tampon.getChannelData(0);
    for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1;
    const src = ctx.createBufferSource(); src.buffer = tampon;
    const filtre = ctx.createBiquadFilter();
    filtre.type = type;
    filtre.frequency.setValueAtTime(coupure, t);
    if (chute) filtre.frequency.exponentialRampToValueAtTime(Math.max(60, chute), t + duree);
    const g = ctx.createGain();
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + duree);
    src.connect(filtre); filtre.connect(g); g.connect(maitre); if (envoi) g.connect(envoi);
    src.start(t); src.stop(t + duree);
  }

  /* ---- les bruits du jeu ---- */

  // Le coup dans le vide : un souffle grave qui fend l'air. Plus de sifflement criard.
  function coup() {
    souffle({ duree: 0.20, coupure: 2600, chute: 480, vol: 0.34 });
    note({ f1: 240, f2: 90, duree: 0.16, forme: 'triangle', vol: 0.10 });
  }

  // L'impact : un choc mat et profond, du corps, pas un « ten ».
  function impact() {
    note({ f1: 130, f2: 44, duree: 0.16, forme: 'sine', vol: 0.5 });      // le poids, dans le grave
    note({ f1: 78, f2: 40, duree: 0.20, forme: 'triangle', vol: 0.34 });
    souffle({ duree: 0.11, coupure: 1500, chute: 160, vol: 0.42 });        // la matière
  }

  // Le joueur prend un coup : un grave sourd qui descend, ça se sent dans le ventre.
  function degat() {
    note({ f1: 200, f2: 84, duree: 0.16, forme: 'triangle', vol: 0.42 });
    note({ f1: 120, f2: 55, duree: 0.24, forme: 'sine', vol: 0.34, retard: 0.05 });
    souffle({ duree: 0.16, coupure: 900, chute: 220, vol: 0.26, retard: 0.02 });
  }

  // Un pas : très court, très sourd, volontairement discret.
  let piedGauche = true;
  function pas() {
    piedGauche = !piedGauche;
    souffle({ duree: 0.045, coupure: piedGauche ? 420 : 360, chute: 120, vol: 0.22 });
  }

  // Objet ramassé : deux notes qui montent, c'est la récompense.
  function ramasse() {
    note({ f1: 660, duree: 0.07, forme: 'triangle', vol: 0.30 });
    note({ f1: 990, duree: 0.12, forme: 'triangle', vol: 0.28, retard: 0.07 });
  }

  // Porte ou escalier : de la pierre lourde qui coulisse, longue et grave.
  function porte() {
    note({ f1: 62, f2: 120, duree: 0.55, forme: 'triangle', vol: 0.24, glisse: 'lin' });
    souffle({ duree: 0.6, coupure: 480, chute: 130, vol: 0.24, type: 'lowpass' });
    note({ f1: 40, f2: 30, duree: 0.7, forme: 'sine', vol: 0.16, retard: 0.05 });
  }

  // La mort : un glas grave qui descend, avec la traînée de la salle.
  function mort() {
    const notes = [220, 165, 123, 82];
    notes.forEach((f, i) => {
      note({ f1: f, f2: f * 0.92, duree: 0.5, forme: 'sine', vol: 0.34, retard: i * 0.2 });
      note({ f1: f / 2, f2: f / 2 * 0.92, duree: 0.5, forme: 'triangle', vol: 0.18, retard: i * 0.2 });
    });
  }

  return { demarrer, volume, coup, impact, degat, pas, ramasse, porte, mort };
})();

if (typeof module !== 'undefined') module.exports = Sons;

if (typeof window !== "undefined") window.Sons = Sons;
