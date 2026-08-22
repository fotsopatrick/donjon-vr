# -*- coding: utf-8 -*-
"""camera_lib — BIBLIOTHÈQUE DE CAMÉRAS DE VALIDATION (P0, étape 4).

La preview artistique doit être reproductible et choisissable. Modes :
  reference_match : reproduit la composition de la référence (hauteur,
                    distance, angle, cible, focale fournis par la SceneSpec)
  cinematic      : vue 3/4 élevée, bassin dominant, profondeur
  overview       : vue de dessus, lecture globale
  gameplay       : vue basse proche (ce que verrait le joueur)

Le mode est choisi par la SceneSpec (champ "camera") ; les paramètres
approximatifs de reference_match viennent de spec["camera"] (dict).
"""
import math

MODES = ("reference_match", "cinematic", "overview", "gameplay")


def mode_depuis_spec(scene_spec, defaut="cinematic"):
    """(mode, spec_cam) : str -> mode simple ; dict -> reference_match avec
    ces paramètres (hauteur/distance/angle/cible/focale)."""
    cam = (scene_spec or {}).get("camera")
    if isinstance(cam, str) and cam in MODES:
        return cam, None
    if isinstance(cam, dict):
        return "reference_match", cam
    return defaut, None


def parametres(mode, R, H, L, P, spec_cam=None):
    """Renvoie (location, cible, fov_deg) pour un mode de caméra."""
    spec_cam = spec_cam or {}
    if mode == "reference_match":
        d = float(spec_cam.get("distance", R * 1.15))
        h = float(spec_cam.get("hauteur", R * 1.45))
        loc = (float(spec_cam.get("ox", 0.0)), -d, h)
        tgt = (float(spec_cam.get("tx", 0.0)),
               float(spec_cam.get("tz", 0.0)),
               float(spec_cam.get("ty", R * 0.22)))
        fov = float(spec_cam.get("fov", 45.0))
        return loc, tgt, fov
    if mode == "cinematic":
        return (0.0, -R * 1.15, R * 1.45), (0.0, 0.0, R * 0.22), 45.0
    if mode == "overview":
        return (0.0, 0.0, R * 2.4), (0.0, 0.0, 0.0), 50.0
    if mode == "gameplay":
        return (0.0, -R * 0.8, R * 0.9), (0.0, 0.0, R * 0.3), 60.0
    return (0.0, -R * 1.15, R * 1.45), (0.0, 0.0, R * 0.22), 45.0


def regler(cam, empty, mode, R, H, L, P, spec_cam=None):
    """Applique la caméra (position, cible, focale) de façon reproductible."""
    loc, tgt, fov = parametres(mode, R, H, L, P, spec_cam)
    cam.location = loc
    try:
        cam.data.angle = math.radians(fov)
    except Exception:
        pass
    empty.location = tgt
    return {"mode": mode, "location": loc, "target": tgt, "fov": fov}
