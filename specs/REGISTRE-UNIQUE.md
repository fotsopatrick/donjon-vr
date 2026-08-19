# KOTOAGE — deux registres d'exploits, séparés par défaut

*Conception du 19/08/2026. Correction de Patrick : NE PAS fusionner d'office la
vie et le jeu. Deux registres distincts ; la fusion est un choix du joueur, et
son utilité n'est pas prouvée aujourd'hui.*

## L'idée en une phrase

Les compétences PROFESSIONNELLES et les compétences de JEU restent **séparées
par défaut**. Elles partagent le même moteur (`equipe.exploit`, le même
garde-fou), mais dans **deux registres distincts** — un pour la vie, un pour le
jeu. Un joueur PEUT choisir de les fusionner ; ce n'est ni la règle, ni conseillé
tant qu'on n'en voit pas l'usage.

## Pourquoi séparé, et pas fusionné

- Coupler la vie pro à la force de jeu, c'est faire dépendre ton personnage de
  ta recherche d'emploi — la plupart des joueurs n'en veulent pas.
- Les deux n'ont pas le même public : le jeu se partage, la carrière est privée.
- On ne gâche rien : le moteur est commun, seule la fusion des compteurs est
  optionnelle. On garde la porte ouverte sans l'imposer.

## Ce n'est pas une idée neuve — c'est un fil déjà à moitié tendu

`CARRIERE-QUESTFORGE-GAP.md` (chantier `garde-index` sur le VPS) le dit noir sur
blanc. La tour a DÉJÀ :

- `tour_equipage` : XP, niveaux, compétences, avec le registre `equipe.exploit`.
- `tour_entretiens`, `tour_cv`, le collecteur de missions : la vie
  professionnelle de Patrick, déjà suivie.

Ce qui MANQUE, et que cette piste comble :

- **une quête réelle terminée → XP réel** (rien ne relie encore une quête à
  `equipe.exploit`) ;
- **la roue des domaines de vie** (santé, carrière, finances, relations,
  formation, maison) — aucun modèle de domaine aujourd'hui ;
- **des quêtes narratives avec XP** — l'onglet actuel est en localStorage,
  perdu au changement de navigateur, sans lien avec l'XP.

KOTOAGE et la carrière ne sont donc pas deux chantiers : c'est **le même moteur,
sur deux terrains.**

## La règle qui tient tout : jamais de point sans registre

C'est le garde-fou de `tour_equipage`, et il vaut pour les deux mondes :

- Aucun point ne s'inscrit sans qu'on puisse dire OÙ il a été gagné.
- La compétence s'arrache, jamais ne se reçoit — que ce soit un piège qui a tué
  dans le donjon, ou un entretien décroché dans la vraie vie.
- Pas de jauge inventée, pas de niveau qui monte pour faire joli.

C'est ce qui sépare une barre de progression décorative d'une vraie évolution.
Et c'est déjà la règle de Patrick.

## La Voix du Monde est le pont

Le même agent accompagne le joueur dans le jeu et dans la vie (voir
[[KOTOAGE-VOIX-DU-MONDE]]). Elle observe ses exploits des deux côtés, les porte
au registre unique, conseille et optimise — bornée, toujours, par ses outils. Le
joueur ne reçoit pas un assistant : il élève le sien, exactement comme Rimuru
élève Raphaël en bâtissant sa nation.

## Comment ça s'emboîte, concrètement (le chantier, pour plus tard)

1. **Deux registres, un moteur** : `equipe.exploit` sait déjà inscrire un
   exploit. On tient DEUX carnets — `pro` et `jeu` — alimentés séparément.
   Le jeu écrit via le serveur qui arbitre ; la vie, via les modules carrière
   existants. Aucun ne déborde sur l'autre.
2. **Chaque exploit taggé par domaine** DANS son carnet : un gardien battu →
   « courage » du carnet jeu ; une candidature → « carrière » du carnet pro.
3. **La roue des domaines**, une par carnet — deux vues, jamais mélangées par
   défaut.
4. **La fusion, en OPTION** : le joueur qui le veut coche « ne faire qu'un ».
   Alors les deux carnets s'agrègent en une seule roue et une seule force. Tant
   qu'il ne le fait pas, sa force de jeu ne dépend QUE de son jeu, et sa
   progression pro reste à part. **Utilité non prouvée — à garder comme
   possibilité, pas comme chemin par défaut.**

## Ce qui reste vrai des décisions déjà prises

- **En multijoueur, le code arbitre l'état partagé** (voir [[KOTOAGE-DECISIONS]],
  « ville partagée + donjon copié », graine commune). Le registre personnel, lui,
  reste au joueur.
- **Faire évoluer son système n'est pas de la triche, c'est le jeu.** Le registre
  ne juge pas qui a le droit d'être fort ; il garde seulement la trace d'où la
  force vient. La cohérence, pas la police.

**Pas pour maintenant. Direction, pas chantier.**
