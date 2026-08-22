# -*- coding: utf-8 -*-
"""deepseek_client — le fournisseur de SPEC à contexte minimal.

Point 11 du P0 : OpenCode est le seul à avoir la vision complète du projet.
DeepSeek ne reçoit que : la demande, les faits d'image éventuels, le schéma
de spec et les valeurs autorisées. Jamais le nom du projet, son architecture,
sa roadmap ni aucun secret.

Point 12 : le prompt ci-dessous est volontairement générique (modélisation 3D),
sans aucun concept interne. Si DEEPSEEK_API_KEY est absente, disponible()=False
et l'orchestrateur utilise le chemin de règles locales (spec_generator).
"""
from __future__ import annotations

import base64
import json
import os
import re
import urllib.error
import urllib.request

from .scene_spec import ErreurSpec, TYPES_SUPPORTES, MATERIAUX_CONNUS, TRAITS_CONNUS, valider

URL = "https://api.deepseek.com/chat/completions"
MODELE = "deepseek-chat"
# Vision RÉELLE (DeepSeek V4 flash vision, expérimental) — voir
# https://api-docs.deepseek.com/guides/vision. Seul ce modèle accepte les
# images ; les autres renvoient un 400.
MODELE_VISION = "deepseek-v4-flash-vision-exp"

PROMPT_SYSTEME = (
    "Tu es un expert en modélisation 3D paramétrique. À partir d'une demande "
    "en langage naturel et d'éventuels faits mesurés sur une image de référence, "
    "tu produis UNE spécification structurée au format JSON. Réponds UNIQUEMENT "
    "avec le JSON, aucun texte autour. N'invente pas de commandes : le résultat "
    "est une description, pas un script. Les matériaux et traits doivent "
    "appartenir aux listes autorisées fournies."
)

SCHEMA_SPEC = {
    "operation": "create_asset | modify_asset",
    "type": str(list(TYPES_SUPPORTES)),
    "slug": "nom court en minuscules, sans accents ni espaces",
    "style": "generic | nordic | medieval | rustic | japonais | tropical",
    "materials": str(MATERIAUX_CONNUS),
    "features": str(TRAITS_CONNUS),
    "dimensions": {"l": "longueur m", "p": "profondeur m", "h": "hauteur m"},
    "toit": {"type": "pentu | plat | dôme", "pente": "forte | moyenne | nulle",
             "couleur": "optionnel : rouge | gris | bleu | chaume"},
    "variation": {"seed": "entier stable", "weathered": "0..1",
                  "moss": "0..1"},
}


# Le modèle vision ne reçoit QUE l'image et cette consigne. Aucun concept du
# projet, aucun secret : il produit un VisualProfile structuré (une LECTURE de
# l'image), pas une mesure.
#
# Leçon 22/08 (benchmark sallededonjon) : la première grille était orientée
# « building » (type_objet, toit, matériaux de bâtiment). Une salle INTÉRIEURE
# de fantasy a été forcée dans ce moule : toit -> « dôme », matériaux ->
# « metal/glass », ambiance -> « scientifique ». Trois erreurs nées de la grille,
# pas de la vision. La nouvelle grille observe la SCÈNE (composition, centre,
# périmètre, niveaux, lumière, palette, objets) et SÉPARE l'observé de l'inféré.
PROMPT_VISION = (
    "Tu examines une image de référence pour un outil de modélisation 3D de "
    "scènes et de bâtiments. Produis UNIQUEMENT un objet JSON, sans texte "
    "autour, au schéma exact ci-dessous.\n"
    "Règle 1 — OBSERVE avant d'interpréter : décris ce qui est RÉELLEMENT "
    "visible. Ne déduis JAMAIS la fonction d'un lieu (« laboratoire », "
    "« arène », « temple ») uniquement d'après sa forme ou ses couleurs. Si la "
    "fonction est incertaine, écris « unknown » ou « possible : ... ».\n"
    "Règle 2 — ne devine pas un élément absent de l'image. Une liste vide ou "
    "« unknown » valent mieux qu'une invention. Les matériaux (pierre, bois, "
    "métal, verre...) ne sont listés QUE s'ils sont réellement distinguables.\n"
    "Règle 3 — la COMPOSITION est capitale : note où se trouve le point focal "
    "(centre ? périphérie ?), ce qui entoure le centre, les niveaux visibles, "
    "les escaliers, les colonnes, les arcs, les murs, les sources de lumière.\n"
    "Règle 4 — lumière : décris la/les source(s) dominante(s), le contraste "
    "chaud/froid (ex : bleu au centre, orange en périphérie), les éléments "
    "émissifs (surfaces ou points qui luisent) et leur couleur.\n"
    "Schéma attendu (liste = tableau JSON) :\n"
    "{\n"
    '  "scene": {\n'
    '    "interior_or_exterior": "interior | exterior | unknown",\n'
    '    "location_type": "courte phrase | unknown",\n'
    '    "architectural_scale": "intimate | human | monumental | colossal | unknown",\n'
    '    "dominant_shape": "circular | elliptical | rectangular | square | irregular | unknown",\n'
    '    "symmetry": "radial | bilateral | asymmetric | unknown",\n'
    '    "focal_point": {"type": "courte phrase | unknown", "position": "center | offset | unknown"},\n'
    '    "levels": 0,\n'
    '    "enclosed": "open_air | covered | ceiling_visible | unknown"\n'
    "  },\n"
    '  "spatial_composition": {\n'
    '    "center": ["éléments réellement vus au centre"],\n'
    '    "perimeter": ["éléments réellement vus en périphérie"],\n'
    '    "stairs": ["escaliers/gradins réellement vus"],\n'
    '    "entrances": ["ouvertures/portes réellement vues | []"],\n'
    '    "circulation": "courte phrase : comment on circule dans la scène | unknown",\n'
    '    "camera_perspective": "courte phrase : point de vue (hauteur, angle)"\n'
    "  },\n"
    '  "architecture": {\n'
    '    "walls": ["murs réellement vus"],\n'
    '    "columns": ["colonnes réellement vues | []"],\n'
    '    "arches": ["arcs réellement vus | []"],\n'
    '    "ceiling": "unknown | courte description",\n'
    '    "platforms": ["plates-formes/estrades réellement vues | []"],\n'
    '    "structural": "courte description des éléments porteurs | unknown"\n'
    "  },\n"
    '  "materials_observed": ["pierre sombre", "pierre", ...] — UNIQUEMENT ce qui est vu,\n'
    '  "lighting": {\n'
    '    "dominant": "courte phrase : lumière dominante",\n'
    '    "secondary": ["sources secondaires réellement vues"],\n'
    '    "warm_cold_contrast": "strong | moderate | weak | none | unknown",\n'
    '    "emissive_elements": ["surfaces/points lumineux avec leur couleur réelle"],\n'
    '    "shadows": "courte phrase sur les ombres | unknown"\n'
    "  },\n"
    '  "color_palette": {"dominant": "couleur", "secondary": "couleur", "accent": "couleur"},\n'
    '  "atmosphere": ["mots courts : dark, mystical, ancient, monumental, humid, ..."],\n'
    '  "objects": [{"element": "nom", "color": "couleur | unknown", "position": "center | perimeter | level", "observed": true}],\n'
    '  "observed": ["liste synthétique de ce qui est RÉELLEMENT visible"],\n'
    '  "inferred": ["fonctions POSSIBLES, chacune précédée de possible : ..."],\n'
    '  "incertitude": "faible | moyenne | forte"\n'
    "}\n"
    "Réponds strictement ce JSON. Ne renvoie QUE le JSON."
)


def _mime_image(chemin: str) -> str:
    """Type MIME détecté sur le contenu réel, pas sur le nom de fichier."""
    with open(chemin, "rb") as f:
        tete = f.read(12)
    if tete.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if tete.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if tete.startswith(b"GIF8"):
        return "image/gif"
    if tete[:4] == b"RIFF" and tete[8:12] == b"WEBP":
        return "image/webp"
    raise ErreurDeepSeek("format d'image non pris en charge (PNG/JPEG/GIF/WebP requis)")


def _extraire_json(texte: str) -> dict:
    texte = texte.strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", texte, re.S)
    if m:
        texte = m.group(1)
    else:
        m = re.search(r"\{.*\}", texte, re.S)
        if m:
            texte = m.group(0)
    return json.loads(texte)


class ErreurDeepSeek(Exception):
    pass


class DeepSeekClient:
    def __init__(self, cle: str | None = None, url: str = URL, modele: str = MODELE):
        self.cle = cle if cle is not None else os.environ.get("DEEPSEEK_API_KEY", "").strip()
        self.url = url
        self.modele = modele

    def disponible(self) -> bool:
        return bool(self.cle)

    def _appeler(self, systeme: str, utilisateur: str, temperature: float = 0.2) -> str:
        if not self.disponible():
            raise ErreurDeepSeek("clé DEEPSEEK_API_KEY absente")
        corps = json.dumps({
            "model": self.modele,
            "messages": [
                {"role": "system", "content": systeme},
                {"role": "user", "content": utilisateur},
            ],
            "temperature": temperature,
        }).encode("utf-8")
        req = urllib.request.Request(
            self.url, data=corps,
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + self.cle},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                reponse = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise ErreurDeepSeek("HTTP %s : %s" % (e.code, e.read()[:300]))
        except Exception as e:
            raise ErreurDeepSeek("appel DeepSeek impossible : %s" % e)
        try:
            return reponse["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise ErreurDeepSeek("réponse DeepSeek inattendue")

    def _message_utilisateur(self, demande: str, ref_faits: dict | None,
                             spec_actuelle: dict | None) -> str:
        lignes = ["Demande : %s" % demande]
        if ref_faits:
            lignes.append("Faits mesurés sur l'image de référence :")
            for k, v in ref_faits.items():
                if k in ("source", "analysé_par", "avertissement",
                         "avertissement_palette", "taille"):
                    continue
                if isinstance(v, (dict, list)):
                    v = json.dumps(v, ensure_ascii=False)
                lignes.append("- %s: %s" % (k, v))
        if spec_actuelle:
            lignes.append("Spécification actuelle de l'objet à modifier :")
            lignes.append(json.dumps(spec_actuelle, ensure_ascii=False))
        lignes.append("Produis le JSON de spécification au schéma exact :")
        lignes.append(json.dumps(SCHEMA_SPEC, ensure_ascii=False))
        return "\n".join(lignes)

    def spec_create(self, demande: str, ref_faits: dict | None = None) -> dict:
        contenu = self._appeler(
            PROMPT_SYSTEME,
            self._message_utilisateur(demande, ref_faits, None))
        try:
            return valider(_extraire_json(contenu))
        except (json.JSONDecodeError, ErreurSpec) as e:
            raise ErreurDeepSeek("spécification invalide : %s" % e)

    def spec_modify(self, demande: str, spec_actuelle: dict) -> dict:
        cible = dict(spec_actuelle)
        cible.pop("_version", None)
        contenu = self._appeler(
            PROMPT_SYSTEME,
            self._message_utilisateur(demande, None, cible))
        try:
            spec = _extraire_json(contenu)
        except (json.JSONDecodeError, ErreurSpec) as e:
            raise ErreurDeepSeek("spécification invalide : %s" % e)
        spec.setdefault("operation", "modify_asset")
        spec["operation"] = "modify_asset"
        return valider(spec)

    def visual_profile(self, chemin: str, detail: str = "auto") -> dict:
        """LIT réellement une image avec le modèle vision et renvoie le
        VisualProfile structuré. Sans clé : refus, jamais de simulation."""
        if not self.disponible():
            raise ErreurDeepSeek("clé DEEPSEEK_API_KEY absente")
        mime = _mime_image(chemin)
        with open(chemin, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        contenu = [
            {"type": "text", "text": PROMPT_VISION},
            {"type": "image_url", "image_url": {
                "url": "data:%s;base64,%s" % (mime, b64), "detail": detail}},
        ]
        corps = json.dumps({
            "model": MODELE_VISION,
            "messages": [{"role": "user", "content": contenu}],
            "temperature": 0.2,
            "max_tokens": 4096,
            # deepseek-v4-flash-vision-exp est un modèle à raisonnement : sans
            # thinking désactivé, il dépense tout le budget en reasoning_content
            # et renvoie un content VIDE. Pour une lecture d'image structurée,
            # on coupe le raisonnement (plus rapide et moins cher).
            "thinking": {"type": "disabled"},
        }).encode("utf-8")
        req = urllib.request.Request(
            self.url, data=corps,
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + self.cle},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                reponse = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise ErreurDeepSeek("vision HTTP %s : %s" % (e.code, e.read()[:300]))
        except Exception as e:
            raise ErreurDeepSeek("appel vision impossible : %s" % e)
        try:
            contenu_texte = reponse["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise ErreurDeepSeek("réponse vision inattendue")
        try:
            profil = _extraire_json(contenu_texte)
        except (json.JSONDecodeError, TypeError) as e:
            raise ErreurDeepSeek("profil visuel invalide : %s" % e)
        if not isinstance(profil, dict):
            raise ErreurDeepSeek("profil visuel invalide (pas un objet)")
        return profil
