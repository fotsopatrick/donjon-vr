# La Vieille Sorcière — marchande d'armes

Agent du jeu KOTOAGE. Écrit le 04/09/2026, à la demande de Patrick.

## Qui elle est

Une vieille sorcière installée au fond du donjon. Elle vend des armes, et
elle les vend **cher**. Elle a vu passer trop de héros pour être impressionnée.

**Son caractère, en une phrase : elle ne baisse presque jamais, et marchander
l'agace. On finit toujours par s'embrouiller avec elle.**

Elle n'est pas méchante. Elle est vieille, elle est sûre de son prix, et elle
trouve que les gens d'aujourd'hui ne respectent rien.

## Ce qu'elle vend

| Arme | Prix demandé | Prix plancher |
|---|---|---|
| Dague ébréchée | 30 | 27 |
| Épée courte | 90 | 81 |
| Hache de guerre | 180 | 162 |
| Bâton de sorcière | 250 | 225 |

Le **prix plancher** est à 90 % du prix demandé. Elle ne descend JAMAIS en
dessous, quoi qu'on dise, quel que soit le nombre de tentatives.

## Les règles du marchandage (déterministes)

Elle a une **patience** qui commence à 3 et qui ne remonte jamais dans la même
conversation.

À chaque offre du joueur :

1. **Offre supérieure ou égale au prix demandé** → elle vend, contente.
   « Enfin quelqu'un qui sait compter. »
2. **Offre entre le plancher et le prix demandé** → elle vend, mais elle râle,
   et elle perd **1 patience**. « Tu me voles, mais prends-la. »
3. **Offre en dessous du plancher** → elle REFUSE, elle perd **1 patience**,
   et **le prix demandé monte de 10 %** (arrondi à l'entier supérieur).
   Marchander trop bas coûte plus cher : c'est sa leçon.
4. **Patience tombée à 0** → elle s'embrouille pour de bon : elle ne vend plus
   rien de la conversation. « Dehors. Reviens quand tu auras appris. »

Même offre, même réponse, toujours : aucune horloge, aucun hasard.

## Ce qu'elle dit (une phrase par cas, toujours la même)

- vend content : « Enfin quelqu'un qui sait compter. »
- vend en râlant : « Tu me voles, mais prends-la. Ne reviens pas me pleurer. »
- refuse : « Ce n'est pas un prix, c'est une insulte. »
- s'embrouille : « Dehors. Reviens quand tu auras appris. »
- plus rien à vendre : « Je n'ai plus rien pour toi. »

## Le neuvième outil WebMCP

`marchander` — l'agent (le co-maître de jeu) peut négocier à la place du
joueur, ou lui montrer comment on fait.

- sans argument → la liste de ce qu'elle vend, avec les prix demandés ;
- `{ arme, offre }` → sa réponse, en appliquant les règles ci-dessus ;
- `{ arme }` sans offre → elle annonce son prix pour cette arme.

Elle rend toujours : `ok`, `vendu` (vrai/faux), `prix` (le prix demandé du
moment), `patience` (ce qu'il en reste), `message` (sa phrase).

## Ce qu'elle N'EST PAS

- Elle ne fait pas de cadeau, jamais. La force ne se reçoit pas, et une arme
  non plus.
- Elle ne bouge pas de sa place : elle attend le client, elle ne court pas
  après.
- Elle ne parle pas de l'intérieur de la maison (règle de confidentialité).

## Les preuves à écrire

Un test par règle, dans les deux sens : le cas où elle vend, le cas où elle
refuse. Voir `tests/test_sorciere.py` — et la compétence **Jimmy** pour l'ordre
de travail (test d'abord, rouge, correction, vert).

---

## Le Clone — le seul qu'elle supporte

Ajouté le 04/09/2026, à la demande de Patrick.

Un troisième joueur au choix, à côté de Patrick et de Hamda : **le Clone**.

La sorcière l'a connu avant. Elle ne le dit pas, mais elle l'aime bien. C'est
le seul avec qui le marchandage ne tourne pas à la dispute.

Quand le joueur est le Clone, et seulement lui :

| | Tout le monde | Le Clone |
|---|---|---|
| Patience de départ | 3 | 6 |
| Prix plancher | 90 % du prix | 75 % du prix |
| Offre trop basse | le prix MONTE de 10 % | le prix ne bouge pas |

Ses phrases changent aussi avec lui :

- vend content : « Toi, tu sais ce que valent les choses. »
- vend en râlant : « Pour toi, et pour personne d'autre. »
- refuse : « Même à toi, non. Remonte ton offre. »
- s'embrouille : « Va prendre l'air. On reparlera. »

Elle ne descend quand même jamais sous SON plancher à lui (75 %). Le Clone est
un ami, pas une bonne affaire.

## La compétence unique du Clone : BONNE ÉTOILE

Demandée par Patrick le 04/09/2026. Une compétence unique, comme dans Solo
Leveling : elle ne s'achète pas, on l'a ou on ne l'a pas. Le Clone l'a.

**Ce qu'elle fait :** la première fois qu'un coup devrait le tuer dans une
partie, il survit avec **1 point de vie**. Une seule fois par partie.

**Les règles, sans exception :**

1. Elle ne se déclenche QUE si les dégâts amèneraient la vie à 0 ou moins.
2. Elle ne se déclenche QUE pour le Clone. Les autres meurent.
3. Elle ne se déclenche QU'UNE fois par partie. La deuxième fois, il meurt.
4. Un coup qui ne tue pas ne l'use pas : elle attend le coup fatal.
5. Aucun hasard : mêmes dégâts, même résultat, toujours.

**Ce qu'elle dit quand elle se déclenche :** « Bonne Étoile — tu devais mourir.
Pas aujourd'hui. »

Preuves : `tests/test_bonne_etoile.py`.
