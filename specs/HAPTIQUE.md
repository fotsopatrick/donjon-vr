# KOTOAGE — la boucle du corps : chatouille, rire, douleur

*Idée de Patrick, 19/08/2026. Pour plus tard (demande un casque + un peu de
matériel). Notée pour ne pas la perdre — elle est trop belle.*

## L'idée en une phrase

Quand on prend un coup dans le jeu, un appareil **chatouille** le joueur ; le
joueur **rit** malgré lui ; le micro entend le rire et le transcrit en **cri de
douleur** du personnage. Ta réaction involontaire devient une arme du donjon
contre toi.

## Pourquoi ce n'est pas qu'une blague

C'est le thème de KOTOAGE poussé à l'absurde. Kotoage = « élever le mot » : le
monde obéit à ce qu'on prononce. Ici, **même le rire involontaire devient un mot
que le monde prend au pied de la lettre.** Le joueur ne maîtrise plus sa propre
voix, et le donjon s'en sert. C'est le premier jeu où « essayer de ne pas rire »
est une compétence de survie.

## Deux niveaux de matériel

**Facile, déjà dans le casque** : les manettes du Quest ont un moteur de
vibration, piloté par WebXR (`source.gamepad.hapticActuators[0].pulse(force,
durée)`). `blesser()` existe déjà : une ligne, et les mains vibrent au coup.
Aucun matériel en plus.

**Sur le corps (l'idée « chatouille »)** : un appareil séparé, en bricolage —
l'ESP32 du kit de Patrick + de petits moteurs vibrants (ceux d'un téléphone) sur
un brassard/gilet. Le jeu envoie un signal à l'ESP32 quand un coup tombe ;
l'ESP32 fait vibrer près de l'endroit touché. C'est le gilet haptique du
commerce (bHaptics), version maison. Lien par WiFi (marche même sans Bluetooth
sur nomi) ou par le Bluetooth du Quest.

## La vérité sur « guili guili »

Une vraie chatouille, personne ne sait la reproduire : c'est pression + mouvement
+ surprise que le cerveau interprète. Le matériel **vibre** — une vibration
douce et brève évoque le picotement, drôle et surprenant, sans être la vraie
sensation. **Rester sur les moteurs vibrants.** L'électro-stimulation (TENS)
donnerait un fourmillement plus proche, mais on ne met PAS d'électricité sur le
corps pour un jeu : moteurs vibrants seulement, c'est sûr et doux.

## La boucle rire → douleur

- Le micro sert déjà aux sorts (les mots). Pour le rire, on ajoute une **écoute
  de l'énergie sonore** (Web Audio : amplitude + grain de la voix) — pas une
  vraie reconnaissance de rire (IA lourde), mais un détecteur de « soudain tu
  vocalises fort » qui attrape le rire très bien.
- Défaut assumé : il attrapera aussi un cri, un bruit. D'où le **calibrage**.
- « Cri de douleur » = un son + la réaction de coup. Trivial.

## Le sel : le risque

Tant que tu ris, tu es **vulnérable** : l'ennemi frappe plus fort, ta jauge fond.
Le combat devient un duel avec soi-même — rester de marbre pendant qu'on te
chatouille, sinon le donjon te dévore.

## Règles de conception

- **Option**, calibrable en intensité, débrayable d'un bouton. Se faire
  chatouiller à CHAQUE coup deviendrait insupportable, pas amusant : un pic
  court, pas un supplice continu.
- Chatouille et rire→douleur vont ensemble : l'une provoque, l'autre punit.
- Rien d'électrique sur le corps. Vibration seulement.

**Direction, pas chantier. Demande le casque d'abord.**
