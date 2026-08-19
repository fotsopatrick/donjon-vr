# Ce qui coûte cher, et ce qui ne coûte rien

*Relevé du 19/08/2026, mesuré sur nomi. Chaque chiffre ici a été payé en
temps. On les note pour ne pas les repayer.*

## La machine sur laquelle tout ceci a été mesuré

Lenovo ThinkCentre M70t (tour, 13,6 L) · Intel i7-10700, 16 fils ·
**7 Go de RAM** · disque NVMe SK Hynix 238 Go ·
**Intel UHD Graphics 630 — carte intégrée, pas dédiée.**

C'est ce dernier point qui décide de tout. Le processeur est bon ; c'est la
puce graphique qui plafonne.

## Les trois postes de coût, dans l'ordre où on les a découverts

### 1. Les appels de dessin — le vrai coupable

Un « appel de dessin », c'est une fois où le programme dit à la carte
graphique : *dessine cet objet*. Chaque objet séparé en vaut un.

| Situation | Appels | Images/s |
|---|---|---|
| donjon seul, low-poly | 7 à 20 | **60** |
| village, chaque objet posé séparément | 639 | 23 |
| après fusion des maisons et semis instancié | 245 | 24 |

**Une carte intégrée sature vers 200-300 appels.** Deux remèdes, tous deux en
place dans le code :

- **`semer(nom, places)`** — pose N copies d'un modèle en une seule fournée
  (`InstancedMesh`). Soixante-dix arbres coûtent autant qu'un seul.
- **`fondre(groupe)`** — fusionne tous les morceaux d'un groupe qui partagent
  la même matière. Une maison à colombages passe de quarante poutres à quatre
  blocs. L'image est identique.

### 2. Le calcul par pixel

Mesuré sur la démo photoréaliste : **25 images/seconde**, et seulement 30 en
ne laissant qu'**un seul** rocher de 7 000 triangles. Le contenu n'y était
pour rien — c'était le shader.

- `MeshStandardMaterial` calcule la lumière **par pixel** (photoréaliste, cher).
- `MeshLambertMaterial` la calcule **par sommet** (suffisant, rapide).
- `scene.environment` (éclairage par image du ciel) : cher. **En fond seul
  (`scene.background`), c'est gratuit.**

D'où le parti pris retenu : **de vraies textures photographiées sur un
éclairage simple.** La matière vient de l'image, pas du calcul.

### 3. La définition et les ombres

- `setPixelRatio(1.5)` → `1` : gain immédiat, aucune perte visible.
- Ombres 2048 → 768 : moitié moins cher, invisible à l'œil.
- Les ombres coûtent **une passe de rendu entière** : les couper est le
  premier cran de la touche P.

## Ce qui ne coûte RIEN, contre toute intuition

- **La maniabilité.** Courir, foncer, enchaîner, rebondir : quelques dizaines
  d'opérations par image. Un jeu nerveux ne demande aucune puissance.
- **Un ciel photographié** en fond : une seule image, aucun calcul. Il apporte
  montagnes, nuages et horizon pour 1,5 Mo.
- **Les triangles, dans les proportions où l'on travaille.** 67 000 triangles
  ne gênent pas ; 245 appels de dessin, si.

## Le Gaussian Splatting

Une scène reconstruite à partir de photographies, faite de taches de couleur
et non de triangles. Essayé avec **Spark** (`demo-splat.html`) : 177 000
taches, photoréalistes, **en un seul appel de dessin**.

- **Pour** : photoréalisme impossible à modéliser à la main, coût très bas.
- **Contre** : c'est une scène **capturée**, donc figée. Ni collisions, ni
  monstres, ni lumière qui change.
- **Donc** : parfait pour un lieu fixe (une entrée, une salle, une boutique),
  inutilisable pour un donjon généré au hasard.

## Les pièges qui ont coûté une soirée

1. **`bumpScale` au-delà de ~0,5 casse les normales** : les murs deviennent
   NOIRS en pleine lumière, et l'on croit que la scène est trop sombre.
   Valeur retenue : 0,28.
2. **Depuis Trois.js r155, les lumières sont en unités physiques.** Une valeur
   de 3 ou 5 ne donne rien. Une lampe utile est vers 30-50.
3. **Les modèles Kenney sont réglés « métal pur » (`metalness: 1`).** Sans
   ciel réfléchi, un métal ne renvoie rien : ils sortent **noirs**. Forcer
   `metalness = 0`.
4. **Leur feuillage tire au turquoise** (#70e6d6). On le reteinte à la volée.
5. **Un ciel « puresky » a son paysage effacé** : pas de montagnes, juste du
   blanc. Prendre un panorama complet.
6. **`GLTFLoader` dépend de `BufferGeometryUtils`** dans un dossier voisin :
   il faut respecter l'arborescence `jsm/loaders/` et `jsm/utils/`.
7. **Chrome gèle la boucle d'animation dans un onglet d'arrière-plan.** Toute
   mesure d'images par seconde faite ainsi vaut zéro. Seul un humain devant
   l'écran peut lire ce chiffre.

## Ce qu'il faudrait comme machine

Pas un PC neuf : la tour est bonne. Il manque **une carte graphique dédiée**
(compacte, sans connecteur d'alimentation supplémentaire — vérifier les watts
inscrits sur le bloc avant d'acheter) et **32 Go de RAM**. Le même code, sans
une ligne changée, tournerait deux à cinq fois plus vite.
