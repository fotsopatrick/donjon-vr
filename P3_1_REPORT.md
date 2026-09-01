# P3.1 — Murs du donjon

Date : 23/08/2026

## Modification

- Albedo du mur : `assets/textures/mur-pierre.jpg`.
- `InstancedMesh` et géométrie inchangés.
- Couleur par instance conservée.
- Relief conservé avec `texRelief`, `bumpScale: 0.28`.
- `roughness: 0.72`, `metalness: 0.06`, teinte inchangée.
- Répétition adaptée à la hauteur réelle du mur : `0.95 × (HT / T * 0.95)`.
- Décalage UV déterministe par position d'instance ajouté dans le shader du
  matériau, sans duplication de géométrie ni nouvel appel de dessin.

## Résultat visuel

La photo donne une pierre plus crédible que la texture procédurale et le relief
réagit correctement aux torches. Le décalage UV supprime la répétition exacte du
même motif sur chaque instance.

Une jonction verticale reste visible entre certains blocs : la photo source
n'est pas parfaitement tileable. La répétition est réduite, mais pas éliminée.
La première tentative avec une répétition verticale trop faible a été rejetée,
car elle étirait fortement la pierre. Le ratio physique a ensuite été corrigé.

## Performance

Audit Phase B avant P3.1, étage 1 : `135 appels`.

Audit Phase B après P3.1, étage 1 : `134 appels`.

Le nombre d'appels reste stable. La géométrie instanciée est conservée. Les
indicateurs headless de FPS ne sont pas considérés comme un FPS réel isolé.

## Tests

- `node test-jeu.js` : `67 réussis, 0 échoué`.
- `bash tests/audit-phase-b.sh` : aucune erreur, village, étages 1 à 5,
  arène.
- `bash tests/creatures-donjon.sh` : aucune erreur, rat et spectre présents.
- 7 captures Donjon générées sans erreur.

## Décision

Conserver cette version comme candidat P3.1 pour validation humaine. Ne pas
commencer P3.2 tant que les jonctions et la répétition résiduelle n'ont pas
reçu le verdict visuel.
