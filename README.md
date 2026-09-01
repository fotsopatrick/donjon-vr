# KOTOAGE « Le Petit Donjon »

Un donjon 3D **joué à deux** : toi avec le clavier, et un **co-maître de jeu IA**
(ChatGPT) qui agit **dans le monde réel du jeu** via le protocole [WebMCP](https://modelcontextprotocol.io/specification).

> Conçu pour le **WebMCP Challenge 2026** (OpenAI). Démo live et contact :
> voir plus bas.

[🇫🇷][L?] · [Démo en ligne](#démo-en-ligne) · [Comment ça marche](#comment-ça-marche) ·
[Les 7 outils](#les-7-outils) · [Lancer en local](#lancer-en-local) ·
[Tests](#tests) · [Structure](#structure)

---

## Démo en ligne

**https://storage.googleapis.com/kotoage-webmcp-20260901-133904/index.html**

Testable dans le navigateur intégré de ChatGPT (agent WebMCP) ou dans un Chromium
avec `chrome://flags/#enable-webmcp-testing` activé.

Sans navigateur WebMCP, le jeu se lance et se joue normalement : le pont n'ajoute
**aucune** dépendance au rendu.

## Comment ça marche

- `index.html` est un **module ES** autonome (Three.js + tresse WebGL).
- Il expose un pont `window.__webmcpConnexion` (grille, joueur, murs, pièges,
  créatures, HUD) et charge `webmcp/webmcp.js` (la couche de contrat **pure**).
- Quand le navigateur fournit `document.modelContext`, `webmcp/integration.js`
  enregistre les outils et **branche l'état du jeu en direct** (Proxy `grid`,
  accesseurs `vie`, `pieges`, `defisReleves`…) : chaque action de l'agent devient
  un effet réel — un mur s'ouvre, une créature surgit, le HUD s'écrit.

Sans WebMCP, `integration.js` ne fait rien (testé). Le jeu reste intact.

## Les 7 outils

| Outil | Effet réel dans le jeu |
|---|---|
| `etat_joueur` | renvoie vie/mana/étage/équipement/compteurs |
| `donner_potion` | soigne le joueur (petite +2, grande +6), HUD |
| `ouvrir_mur` | ouvre une case mur (`MUR→SOL`), murs reconstruits en 3D |
| `placer_piege` | pose un piège sur une case sol (mémorisé `dernierPi`) |
| `inspirer` | donne une piste contextuelle (lieu ou étage) |
| `defier` | fait surgir de vrais ennemis (gardien/guerrier/horde) |
| `raconter` | narration d'un étage (1→5, 0 = le hameau) |

Chaque réussite s'affiche dans le HUD du joueur (`dire`).

## Lancer en local

```bash
# serveur statique simple (module ES + GLB ont besoin de HTTP)
python -m http.server 8100
# puis : http://localhost:8100/index.html
```

## Tests

Tous vérifiés, zéro dépendance :

```bash
python tests/test_webmcp.py                # 31 tests — contrat de la couche pure
python tests/test_webmcp_integration.py    # 15 tests — pont réel (harnais DOM)
python tests/test_webmcp_live_cdp.py <url> # vérification navigateur réel (Chrome headless, CDP)
```

`tests/run.sh` regroupe la suite (statiques + comportement).

## Structure

```
index.html                 module de jeu (Three.js, WebGL)
webmcp/
  webmcp.js                couche de contrat WebMCP (pure, double export)
  integration.js           pont réel jeu ↔ document.modelContext
assets/, modeles/, jsm/, … assets 3D (Quaternius, VRM, polyhaven)
tests/                     preuves (Python + harnais Node + CDP live)
deploy/gcloud-deploy.ps1   déploiement Google Cloud Storage (bucket public)
```

## Licence

MIT © 2026 Patrick Fotso