# KOTOAGE — pistes futures (pas pour maintenant)

*Idées de Patrick, 19/08/2026. Notées pour ne pas les perdre. Aucune n'est à
coder tout de suite ; elles fixent la direction.*

## 1. Un seul registre d'exploits, pour la vie ET le jeu

Lier KOTOAGE à la tour de contrôle : l'utilisateur évolue personnellement ET
dans le jeu, à partir du même compteur.

**C'est déjà à moitié écrit.** `CARRIERE-QUESTFORGE-GAP.md` (chantier
garde-index) note que la tour a déjà XP, niveaux, compétences et le registre
`equipe.exploit`, plus la roue des domaines de vie. Ce qui manque : le fil
« quête réelle terminée → XP réel ». Cette piste le tend.

- Un exploit réel (une candidature, un chantier fini, un objectif tenu) s'inscrit
  au MÊME endroit qu'un exploit de jeu, sous le MÊME garde-fou :
  **la compétence s'arrache, jamais de point sans registre.**
- La progression réelle alimente le personnage, et inversement.
- C'est Rimuru à la lettre : sa puissance dans le donjon vient de ce qu'il
  construit pour de vrai dans sa nation.

**La Voix du Monde est le pont.** C'est le Raphaël personnel du joueur — le même
agent dans les deux mondes, qui le suit de la vie au donjon. Voir
[[KOTOAGE-VOIX-DU-MONDE]] (à réécrire en « compagnon-agent à outils » et non
« filtre de traduction » — correction de Patrick du 19/08).

## 2. Le duel réel, façon Pokémon Go

Affronter un autre joueur en vrai, par la proximité. **Gardé pour plus tard
sciemment** — pas parce que l'idée est faible, mais à cause de trois pièges
concrets à régler d'abord :

- **Vie privée** : la géolocalisation est une donnée sensible. Jamais dans une
  URL, jamais centralisée à la légère.
- **Triche** : une position GPS se falsifie. Il faut le serveur déterministe
  qui arbitre — le même Victor que partout.
- **Sécurité physique** : Pokémon Go a causé de vrais accidents. Un système qui
  pousse à se rencontrer porte une responsabilité réelle.

**Mais le combat, lui, est déjà conçu.** Deux joueurs, la même graine de donjon,
le serveur qui arbitre l'état partagé (voir la décision « ville partagée +
donjon copié » et la graine commune dans [[KOTOAGE-DECISIONS]]). Un duel, c'est
ce mécanisme déclenché par la proximité. La couche « réelle » est la partie
fragile ; le combat est prêt sur le papier.

## Ce qui relie ces deux pistes

Le même principe que la tour, du début à la fin : un agent (la Voix) borné par
ce que le code lui autorise, un registre unique où rien ne s'inscrit sans être
mérité, et un arbitre déterministe pour tout ce qui est partagé. Le jeu et la
vie ne sont pas deux systèmes : c'est le même moteur, sur deux terrains.
