# Le banc Braignak / map serveur

    node tests/test_braignak_cdp.mjs [url]

Sans argument : teste la page LIVE du bucket.
Avec une url : teste une copie (ex. index-braignak.html).

Il lance SON PROPRE Chrome (profil jetable, tué à la fin) et vérifie l'état
réel du jeu à travers le pont `window.__webmcpConnexion` :

- le pont répond et expose `changerMap` / `braignakEtudier` ;
- `changerMap('serveur')` met TOUTES les salles en salle serveurs ;
- `changerMap(null)` revient à un donjon varié ;
- une nouvelle étude fait partir Braignak (phase « cherche ») ;
- une étude déjà menée ne le fait PAS partir ;
- choisir DONJON à l'écran-titre arme la salle serveurs, VILLAGE la désarme.

Attendu : `17/17 verts` et code de sortie 0.
