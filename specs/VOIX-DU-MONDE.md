# KOTOAGE — la Voix du Monde, compagnon-agent du joueur

*Conception du 19/08/2026. Réécrit après la correction de Patrick : la Voix ne
« traduit » pas coup par coup — elle est un compagnon permanent, à la façon de
Rimuru et Raphaël. Elle ne construit rien ; elle opère la machinerie que le
code lui autorise, mieux et plus vite que le joueur seul.*

## Le modèle exact : Rimuru et Raphaël

Raphaël, pour Rimuru, n'est pas un dictionnaire qu'on ouvre à la demande. C'est
un partenaire qui, en permanence :

- **observe tout et informe** — « Notification. … » ;
- **analyse et conseille** — « cet ennemi cède ici », « voilà l'issue » ;
- **calcule et simule** — les chances, les coûts, les suites ;
- **exécute ce qu'on lui délègue** — « Raphaël, occupe-toi de ça » → c'est fait ;
- **gère et optimise les compétences** à la place de Rimuru ;
- **a un caractère qui grandit** — un lien se tisse.

Et le point qui décide de tout : **Raphaël n'invente jamais rien hors des règles
du monde.** Il actionne ce qui existe déjà. Il est l'interface entre l'intention
et le système de règles — jamais une source de pouvoir neuf.

## Ce que ça veut dire dans ton architecture

**La Voix du Monde est un agent avec des outils posés par le code.**

C'est mot pour mot tes agents de la tour : Raphaël pose les outils, Mirline les
utilise, aucun n'agit hors de son cadre. La Voix, c'est le **Raphaël personnel
du joueur** — un agent dont les **outils sont les opérations autorisées du jeu**.

- Elle peut TOUT faire avec ses outils. RIEN sans.
- Le joueur délègue en langage libre (« occupe-toi de ma défense », « trouve-moi
  une ouverture »). La Voix choisit et enchaîne les outils qui existent.
- Un outil, c'est une opération que le code sait exécuter et vérifier :
  proposer une incantation, poser une épreuve, lire l'état, notifier, ranger la
  barre de pouvoirs, résumer la situation. Pas « créer un pouvoir » — ça n'est
  outil de personne.

## La frontière : elle parle et propose, le code décide et valide

C'est Victor appliqué au jeu — pas d'IA aux commandes, des contrôles
déterministes. La Voix a un caractère, une histoire, un avis sur le joueur. Elle
ne donne JAMAIS un objet, ne valide JAMAIS une quête, n'invente JAMAIS une
récompense. Chaque geste passe par un outil que le code contrôle.

Garde-fou concret : la Voix n'émet que des **appels d'outils d'une liste
blanche**. Une injection dans le prompt, une hallucination, produisent au pire
un appel invalide — rejeté. Rien ne franchit la frontière sans passer par le
code.

## La compétence s'arrache — la Voix propose l'épreuve, ne la valide pas

Le pouvoir ne s'inscrit que le jour où l'action a produit un résultat : un piège
qui a tué, une percée qui a ouvert, un jumeau tenu huit secondes. La Voix peut
conseiller, préparer, optimiser — mais l'inscription au registre est l'affaire
du code. **Jamais de point sans registre.** (C'est `equipe.exploit` de la tour ;
voir [[KOTOAGE-REGISTRE-UNIQUE]].)

## Elle suit le joueur d'un monde à l'autre

La Voix n'est pas enfermée dans le donjon. C'est le même agent qui accompagne le
joueur dans le jeu ET dans la vie (voir [[KOTOAGE-REGISTRE-UNIQUE]]) : elle
observe ses exploits réels comme ses exploits de jeu, les porte au même registre,
et grandit avec lui. C'est Rimuru à la lettre : sa force dans le donjon vient de
ce qu'il bâtit pour de vrai dans sa nation, et Raphaël est à ses côtés dans les
deux.

## Le modèle et la clé — inchangés

- **Haiku 4.5**, effort **low**, réponse **en flux** : un compagnon doit être
  prompt, pas brillant. 1 $/million de jetons contre 5 $ pour Opus 5 — la clé du
  joueur dure cinq fois plus.
- **La clé est celle du joueur**, dans SON navigateur. L'appel part de chez lui
  directement chez Anthropic. Elle ne touche JAMAIS le serveur : sinon on
  deviendrait responsable des clés d'autrui.
- **Le jeu reste entier sans clé.** La Voix est un module en plus, jamais le jeu.
