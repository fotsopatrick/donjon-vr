# KOTOAGE / Le Petit Donjon — doc du projet

Ce fichier dit **ce que le jeu contient**, **où sont les choses**, **comment le lancer
et le tester**, et **les pièges déjà payés**. À lire au début de chaque session.

Le jeu est un seul gros fichier : `~/donjon-vr/index.html` (Three.js r169, tout en
local). Il ne va jamais sur Internet ; seul le dépôt git va sur la tour.

---

## 1. Lancer et voir le jeu

```
cd ~/donjon-vr && python3 serveur-nocache.py      # sert le jeu sans garder de vieille version
```
Puis ouvrir dans Chrome : `http://127.0.0.1:8099/index.html`
Recharger avec **Ctrl + Maj + R** (les trois touches ensemble : oblige le navigateur
à oublier l'ancienne version — sinon un bug « qui revient » est souvent le cache).

Pour entrer direct dans un lieu (pour tester) : ajouter à l'adresse `#village`,
`#donjon` ou `#arene`.

## 2. Les commandes du jeu

- **Z Q S D** : se déplacer · **Maj** : courir · **Espace** : sauter / voler
- **Souris (clic maintenu)** : regarder autour · **flèches ← →** : tourner
- **Clic gauche** : frapper · **X** : change d'arme (une épée → deux épées → poings)
- **R** : se verrouiller sur un ennemi · **G** : défier le guerrier · **F** : vue 1re/3e personne
- **E** : ouvrir un coffre, prendre un portail · **V** : parler à l'esprit du donjon
- **P** : baisser la qualité quand ça rame (coupe les ombres, éteint des torches)
- **Espace × 2 en vol** : décoller · **Maj** en vol : descendre
- **Mot de passe d'accès** : 3173

## 3. Les lieux

- **Le village** (dehors, niveau 0) : hameau, une route, une forêt, un second village.
  145 mètres de long. Des habitants avec des trajets fixes. `#village`
- **L'arène d'entraînement** (niveau -1) : salle cyberpunk néon, un guerrier à défier,
  vie illimitée. `#arene`
- **Le donjon** (niveaux 1 à 5) : caves, ossuaire, clairière (sans murs), voile, palier.
  Un gardien tous les 5 étages. Chaque étage a sa couleur et sa faune. `#donjon`

## 4. Le combat

- 7 coups d'épée différents (vrais gestes de sabre), qui s'enchaînent quand on clique.
- Deux épées (escrime à deux lames) : plus rapide, moins fort par coup.
- Choc d'épées dans l'arène : quand les deux lames se croisent, on verse son mana
  pour pousser l'autre ; le gagnant traverse la garde, le perdant est sonné.
- Magie : boule de feu, eau, vent ; colonne de feu (attaque suprême) ; compétence
  dépassement (beaucoup d'ondes d'un coup). Le mana et la vie remontent avec le niveau.

## 5. Où sont les choses dans le code (`index.html`)

- **HT** : hauteur du plafond (varie par étage). La boîte du mur se refait à cette
  hauteur — sinon les murs flottent.
- **MOMENTS** + **poserMomentDuJour** : l'éclairage selon l'heure (midi, doré…).
- **NUANCIER / nuancierToon** : le dégradé du style manga (cel-shading). Sa marche la
  plus sombre part d'un plancher (MIN_TOON) pour ne jamais être du noir pur.
- **construireMurs** : dresse la pierre d'après la grille.
- **COUPS_EPEE** : la table des 7 coups d'épée.
- **choc** + **majChoc** : le duel de mana (choc d'épées).
- **animerVRM** / **poserCorpsEnLAir** : les mouvements des personnages, le vol, le saut.
- **trouverOsCorps** + **ALPHABET_OS** : trouve les os d'un personnage, quelle que soit
  la fabrique (VRoid dit « J_Bip_… », Mixamo dit « LeftArm »).
- **poserOs** : tourne un os à partir de sa pose de repos (sinon marche « robot »).
- **maxTorches** : combien de torches (lumières dynamiques) allumées — baissé par la
  touche P quand ça rame.
- **PLAN_ETAGE1** : le plan dessiné à la main de l'étage 1 (# mur, . sol, S départ,
  D sortie, K cercle de téléportation, B boss, C coffre).

## 6. Tester (comme dans un studio)

```
node test-jeu.js            # contrôles statiques (syntaxe + invariants) — rapide
bash tests/run.sh           # + tests de comportement (le jeu piloté dans un navigateur)
SEUL=murs_au_sol bash tests/run.sh   # ne lancer que certains tests
```
Les tests de comportement (dans `tests/runtime.js`) pilotent le vrai jeu et VÉRIFIENT :
amplitude des mouvements, corps entier, frappe, vol, orientation/demi-tour, villageois,
os des villageois, mage, jauge de mana, deux épées, choc d'épées, murs au sol.

Les **sondes** (`tests/sonde-*.js`) répondent chacune à UNE question en mesurant :
accès d'un étage, hauteur des murs, habitants, vol, performance (appels/lumières).

**Règle d'or** : jamais dire « c'est corrigé » sans une capture ou une mesure. Et un
test doit être PATIENT (attendre que la chose soit prête) — sinon il crie au loup.

## 7. La carte vivante du jeu

`node carte/scanner.js` ouvre le jeu, visite chaque lieu, et écrit
`carte/inventaire.json` (ce qui existe VRAIMENT : personnages, décors, cercles,
lumières). La page `carte/index.html` l'affiche avec des onglets par type et une zone
de commentaire par lieu. Raccourci bureau : **« Carte vivante du jeu »**.

## 8. Sauvegarde du code sur la tour

Dépôt nu sur la tour : `~/depots/kotoage.git`, branche `master`.
Depuis nomi : `git push tour master` (agent SSH chargé :
`SSH_AUTH_SOCK=~/.ssh/agent.sock`). Le pack Quaternius téléchargé (`assets/mvmk/`,
169 Mo) est exclu ; les `.vrm` de Patrick (84 Mo) sont gardés.

## 9. Les pièges déjà payés (ne pas refaire)

1. **La duplication ment.** La liste des maisons était lue à 5 endroits ; j'en ai
   changé 2, un village est resté invisible. → une donnée, un seul endroit.
2. **Le cache Chrome ment.** Un bug « qui revient » = souvent l'ancienne version.
   → serveur-nocache + Ctrl+Maj+R + `?t=` dans les tests.
3. **Deux fabriques, deux noms d'os.** Un code qui ne cherche qu'un alphabet laisse
   la moitié des personnages sans os → ils glissent. → ALPHABET_OS parle les deux.
4. **Animer = tourner depuis le repos**, pas en position absolue. Sinon « robot ».
5. **Les bras en croix.** Un VRoid est fabriqué bras tendus ; on les rabat au repos.
6. **Le corps collé à la caméra** faisait marcher en crabe. → cap (corps) séparé de
   lacet (caméra) ; hors combat, le corps se tourne vers là où il va.
7. **Le mur flottant.** La boîte du mur figée à une hauteur mais posée à une autre →
   le bas décollait du sol. → la boîte se refait à la hauteur du lieu.
8. **Le noir dur.** Le cel-shading avait une marche à 0 = noir pur. → plancher MIN_TOON.
9. **Une machine à la fois.** Un navigateur de test sans fenêtre calcule à fond ; en
   empiler plusieurs a fait ronfler le PC à 1135 %. → un seul, fermé aussitôt.
10. **Le vrai frein n'est pas les triangles**, ce sont les appels de dessin et les
    lumières dynamiques. Le chiffre « i/s » (images/seconde) se lit en haut à droite,
    sur un VRAI écran — un test sans écran ment là-dessus.

## 10. Ce qui reste à faire (au 22/08/2026)

Voir `A-FAIRE.md` (rangé par priorité) et `KOTODAMA-tout-ce-que-Patrick-a-demande.md`
sur le bureau. En cours : l'écran noir total à la reprise d'une partie sauvegardée,
l'adversaire d'entraînement qui ne copie pas les mouvements, le colisée d'entrée
incomplet, la photo du ciel posée au sol.
