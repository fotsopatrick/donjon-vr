# Pièges du donjon — notes (à implémenter PLUS TARD)

## L'idée de Patrick (20/08)
**Fils d'acier tendus en travers d'un couloir.** Des câbles/lames fins barrent le passage :
si on ne les **tranche pas** (coup d'épée) avant d'avancer, on est **coupé** (dégâts, voire mort).
→ mécanique : détecter la frappe d'épée sur le fil pour le sectionner ; sinon, franchir la ligne
inflige des dégâts. Visuel : fils fins brillants tendus mur à mur, à hauteur variable.
*(Interprété comme « fils d'acier » ; si tu voulais dire autre chose, redis-le.)*

## Pièges classiques de donjon (banque d'idées)
Déjà dans le jeu : `poserPiege` = pics qui jaillissent du sol.
À ajouter éventuellement :
- **Fosse à pics** — le sol s'ouvre / trou dissimulé au fond hérissé de pointes.
- **Dalle de pression** — marcher dessus déclenche flèches, herse, ou effondrement.
- **Dards / flèches murales** — jets depuis des trous dans le mur en passant.
- **Pendule à lames** — grande lame qui balaie un couloir en rythme (esquive au timing).
- **Herse / mur qui se resserre** — les parois se rapprochent, il faut traverser vite.
- **Bloc qui tombe** — plafond ou rocher qui s'écrase (façon Indiana Jones).
- **Jets de flammes** — souffles de feu périodiques depuis le sol ou les murs.
- **Fil déclencheur (tripwire)** — fil invisible/fin qui arme un autre piège si franchi.
- **Sol en damier piégé** — seules certaines dalles sont sûres.
- **Gaz / poison** — salle qui se remplit, il faut sortir avant de suffoquer.

## Principe de design (cohérent avec la tour : les portes qui refusent gardent)
Un piège n'est pas une punition gratuite : il **teste** (timing, observation, réflexe épée).
Chaque piège doit avoir un **tell** (indice visuel/sonore) et une **parade** (trancher, esquiver, timing).
