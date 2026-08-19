# KOTOAGE — le registre cyber : le donjon des conteneurs

*Idée de Patrick, 19/08/2026. Une peau du même donjon : au lieu de slimes et de
gardiens, des conteneurs Docker. On descend d'un étage en RAISONNANT une faille,
pas en tapant un exploit.*

## Le concept

Chaque étage = un conteneur Docker avec une **faille connue, plantée exprès**.
Le joueur descend en la comprenant : « ce conteneur expose ce port, la version
est celle-ci, donc voilà par où ça cède ». La résolution se fait **par le
raisonnement, en dialoguant** — comme une conversation — et NON en tapant des
commandes d'exploitation.

On enseigne le muscle (raisonner une faille), pas le geste (taper la commande).
C'est la compétence rare et transférable, et peu de jeux l'osent.

## Pourquoi ça EST déjà la tour

Les circuits de la tour ont des **portes**, et une porte est une **épreuve** :
« une porte qui refuse fait son travail ». Baki : la force se débloque, chaque
combat réglé rend plus fort. Un conteneur à percer, c'est une porte fermée dont
la faille est la serrure et le raisonnement la clé. On descend parce qu'on a
compris. Même structure, autre peau — c'est le monde IT de STRATE.

## Le cadre non négociable — c'est Victor

Ce qui sépare un labo de sécurité (éducatif, défensif, légitime, comme un CTF)
d'autre chose :

- **Failles CONNUES, plantées par toi**, jamais découvertes sur une vraie cible.
- **Bac à sable ISOLÉ** : conteneurs jetables, qui ne contiennent QUE la faille
  plantée. Jamais un système réel, jamais un tiers.
- **But = compréhension démontrée**, pas compromission d'un vrai système.

Tant que c'est ton propre conteneur, planté exprès, isolé, c'est de
l'entraînement à défendre en comprenant comment ça casse. Rien d'autre.

## Le garde-fou connu s'applique tel quel

**La Voix dialogue, le code décide.**
- La Voix est l'interlocutrice socratique : elle accompagne, pose des questions,
  confirme les étapes. Elle ne souffle JAMAIS la réponse.
- Le code tient la clé : la faille plantée a un chemin de résolution connu, avec
  des **points de passage** définis. Il vérifie le raisonnement du joueur contre
  ces points. La porte s'ouvre quand ils sont franchis.

## Ce que ça donne au carnet pro

Un raisonnement de sécurité mené jusqu'au bout est une **compétence réelle**.
Elle s'inscrit au **carnet pro** (voir [[KOTOAGE-REGISTRE-UNIQUE]]), séparé du
fantasy. Le donjon des conteneurs est le terrain qui donne enfin corps à ce
carnet — le monde IT à côté du monde fantasy, deux registres du même jeu.

## À décider plus tard

- Le catalogue de failles plantées : lesquelles, quel ordre de difficulté.
- Comment la Voix guide sans souffler (le dosage socratique).
- Si un étage mêle les deux peaux, ou si cyber et fantasy sont deux donjons
  distincts qu'on choisit à l'entrée.

**Direction, pas chantier.**
