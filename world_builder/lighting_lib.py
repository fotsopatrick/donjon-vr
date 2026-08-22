# -*- coding: utf-8 -*-
"""lighting_lib — BIBLIOTHÈQUE DE PRESETS D'ÉCLAIRAGE (P0, étape 5).

L'éclairage n'est plus codé dans la scène : un preset nommé (cinematic_contrast,
dark_fantasy, torchlight, magical_blue, cold_overcast, warm_interior,
moonlight) fournit couleurs, intensités, lune de remplissage et ambiance
monde. La SceneSpec choisit via lighting.preset ; sinon le contraste dérivé
de la vision sélectionne un preset par défaut.

Module PUR (aucun import Blender) : utilisable dans parametrer et en tests.
"""
LUMIERE = {
    # centre bleu/cyan vs périmètre orange chaud — le preset par défaut du
    # benchmark (vient du warm_cold_contrast "strong" de la vision).
    "cinematic_contrast": dict(
        center_color=(0.30, 0.55, 1.0), perimeter_color=(1.0, 0.50, 0.22),
        center_intensity=3600, perimeter_intensity=9500,
        sun_color=(0.60, 0.68, 0.95), sun_energy=0.4,
        world_color=(0.05, 0.06, 0.09), contrast="strong"),
    "dark_fantasy": dict(
        center_color=(0.25, 0.45, 0.90), perimeter_color=(1.0, 0.45, 0.15),
        center_intensity=2000, perimeter_intensity=6000,
        sun_color=(0.40, 0.45, 0.70), sun_energy=0.25,
        world_color=(0.03, 0.04, 0.07), contrast="strong"),
    "torchlight": dict(
        center_color=(1.0, 0.60, 0.30), perimeter_color=(1.0, 0.55, 0.20),
        center_intensity=2000, perimeter_intensity=12000,
        sun_color=(0.50, 0.40, 0.30), sun_energy=0.20,
        world_color=(0.04, 0.03, 0.02), contrast="moderate"),
    "magical_blue": dict(
        center_color=(0.20, 0.50, 1.0), perimeter_color=(0.50, 0.60, 1.0),
        center_intensity=5000, perimeter_intensity=2000,
        sun_color=(0.50, 0.60, 1.0), sun_energy=0.30,
        world_color=(0.03, 0.05, 0.10), contrast="moderate"),
    "cold_overcast": dict(
        center_color=(0.60, 0.65, 0.80), perimeter_color=(0.70, 0.72, 0.80),
        center_intensity=3000, perimeter_intensity=3000,
        sun_color=(0.70, 0.75, 0.90), sun_energy=0.80,
        world_color=(0.10, 0.11, 0.14), contrast="none"),
    "warm_interior": dict(
        center_color=(1.0, 0.60, 0.30), perimeter_color=(1.0, 0.55, 0.25),
        center_intensity=4000, perimeter_intensity=6000,
        sun_color=(1.0, 0.80, 0.60), sun_energy=0.50,
        world_color=(0.08, 0.06, 0.04), contrast="moderate"),
    "moonlight": dict(
        center_color=(0.50, 0.60, 1.0), perimeter_color=(0.60, 0.70, 1.0),
        center_intensity=2500, perimeter_intensity=1500,
        sun_color=(0.60, 0.70, 1.0), sun_energy=0.50,
        world_color=(0.04, 0.05, 0.09), contrast="weak"),
}

# preset par défaut selon le contraste observé (vision)
PAR_CONTRASTE = {
    "strong": "cinematic_contrast",
    "moderate": "torchlight",
    "weak": "moonlight",
    "none": "cold_overcast",
}


def choisir_preset(lumiere_scene: dict, contraste: str = "strong") -> dict:
    """Preset choisi par la SceneSpec (lighting.preset), sinon selon le
    contraste. Retourne le preset COMPLET (fusionné avec le contraste)."""
    nom = (lumiere_scene or {}).get("preset")
    if not isinstance(nom, str) or nom not in LUMIERE:
        nom = PAR_CONTRASTE.get(contraste, "cinematic_contrast")
    preset = dict(LUMIERE[nom])
    # la SceneSpec peut surcharger des valeurs précises (température/intensité)
    for k in ("center_color", "perimeter_color", "center_intensity",
              "perimeter_intensity", "sun_color", "sun_energy", "world_color"):
        if k in (lumiere_scene or {}):
            preset[k] = (lumiere_scene or {}).get(k)
    preset["preset"] = nom
    return preset
