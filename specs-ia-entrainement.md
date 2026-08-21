# Mode entraînement — consignes d'IA de combat (fournies par Patrick, style Naruto Storm)

À appliquer à l'adversaire IA du mode entraînement (le guerrier/jumeau) — hiérarchie de priorités :

1. **Ciblage dynamique** — verrouiller la cible la plus proche ou la plus menaçante (adversaire ou
   boss géant). Changer de cible si la cible actuelle entre en phase d'invulnérabilité ou s'éloigne
   excessivement.
2. **Boucle d'attaque et annulation** — à portée courte, exécuter des combos physiques. Si l'adversaire
   subit une projection, exécuter immédiatement un dash offensif (consommant de la ressource) pour
   intercepter la cible avant qu'elle ne se rétablisse.
3. **Mobilité contre boss géants** — à moyenne distance, si détection d'une attaque de zone (AOE)
   balayante d'un boss géant, effectuer une esquive/dash latéral avant de foncer vers la cible.
4. **Gestion des ressources** — recharger la ressource de mobilité/attaque uniquement lorsqu'une
   distance de sécurité est établie et qu'aucune attaque adverse n'est imminente.

Structure possible : Behavior Tree, FSM, ou Utility AI. → à implémenter dans `majGuerrier` / l'IA du jumeau.
