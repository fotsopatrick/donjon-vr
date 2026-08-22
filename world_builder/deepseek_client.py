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

import json
import os
import re
import urllib.error
import urllib.request

from .scene_spec import ErreurSpec, TYPES_SUPPORTES, MATERIAUX_CONNUS, TRAITS_CONNUS, valider

URL = "https://api.deepseek.com/chat/completions"
MODELE = "deepseek-chat"

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
