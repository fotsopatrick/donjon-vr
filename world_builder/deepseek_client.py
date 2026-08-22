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
    "toit": {"type": "pentu | plat", "pente": "forte | moyenne | nulle",
             "couleur": "optionnel : rouge | gris | chaume"},
    "variation": {"seed": "entier stable", "weathered": "0..1",
                  "moss": "0..1"},
}


# Le modèle vision ne reçoit QUE l'image et cette consigne. Aucun concept du
# projet, aucun secret : il produit un VisualProfile (une LECTURE de l'image),
# pas une mesure. Pour tout ce qu'il ne voit pas avec certitude, il renvoie
# vide plutôt que de deviner — on ne prétend jamais qu'une image est comprise
# si elle ne l'est pas.
PROMPT_VISION = (
    "Tu examines une image de référence pour un outil de modélisation 3D de "
    "bâtiments. Produis UNIQUEMENT un objet JSON, sans texte autour, au schéma "
    "exact ci-dessous. Décris UNIQUEMENT ce que tu vois réellement dans l'image. "
    "Pour tout champ que tu ne peux pas déterminer avec certitude, mets une "
    "chaîne vide ou une liste vide — ne devine jamais.\n"
    "Schéma attendu :\n"
    "{\n"
    '  "type_objet": "building" ou "",\n'
    '  "architecture": "description courte en français, 2 à 8 mots (ex : maison nordique à toit pentu)",\n'
    '  "style": "nordic | medieval | rustic | japonais | tropical | generic | ", \n'
    '  "materiaux_visibles": liste prise dans ["dark_wood","wood","aged_stone","stone","plaster","moss","thatch"] — vide si incertain,\n'
    '  "traits_visibles": liste prise dans ["steep_roof","weathered_wood","moss","chimney","porch","balcony"] — vide si incertain,\n'
    '  "couleurs": ["brun foncé","gris pierre","rouge","chaume",...] — noms de couleurs réellement vus,\n'
    '  "toit": {"type": "pentu | plat | ", "pente": "forte | moyenne | nulle | ", "couleur": "rouge | gris | chaume | "},\n'
    '  "proportions": {"l": 0.0..1.0, "p": 0.0..1.0, "h": 0.0..1.0} — ratios RELATIFS entre les dimensions de l\'objet vu (ex : l=1.0, p=0.8, h=0.9), JAMAIS des mètres,\n'
    '  "ambiance": liste courte de mots ["nuit","brouillard","froid","humide","ensoleillé","chaleureux",...],\n'
    '  "incertitude": "faible | moyenne | forte"\n'
    "}\n"
    "Réponds strictement ce JSON."
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
                if k in ("source", "analysé_par", "avertissement", "taille"):
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
