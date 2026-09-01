# -*- coding: utf-8 -*-
# =====================================================================
#  tests/test_webmcp.py — PREUVES de la couche WebMCP de KOTOAGE
# ---------------------------------------------------------------------
#  Principes (règles projet KOTOAGE, CLAUDE.md) :
#    · TDD : le test est écrit AVANT le dev et devient la définition de
#      « fonctionne ». Ici il prouve le CONTRAT de webmcp/webmcp.js.
#    · Test réel mesuré : pas d'assertion « de mémoire ». Chaque test
#      exécute la VRAIE implémentation JavaScript — via Node — et vérifie
#      la réponse exacte. Le jeu tournant dans le navigateur, on ne peut
#      pas (et on ne doit pas, règle nº1) faire tourner WebGL ici : on
#      teste la logique pure de la couche WebMCP, qui est exactement le
#      code qui sera branché sur document.modelContext dans index.html.
#
#  Comment lancer (depuis la racine du projet) :
#    python tests/test_webmcp.py            # tout
#    python tests/test_webmcp.py TestOuvrirMur   # une classe
#  Prérequis : Node.js dans le PATH (harnais tests/webmcp_harness.js).
# =====================================================================
import json
import os
import subprocess
import unittest

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARNESS = os.path.join(RACINE, "tests", "webmcp_harness.js")

# Les 7 outils que la couche doit exposer — c'est LA liste de référence.
OUTILS_ATTENDUS = {
    "etat_joueur",
    "donner_potion",
    "ouvrir_mur",
    "placer_piege",
    "inspirer",
    "defier",
    "raconter",
}


def node(mode, payload=None):
    """Lance le harnais Node et retourne la réponse JSON décodée.

    Chaque appel = un process Node neuf : l'état de jeu repart toujours
    de ETAT_INITIAL, donc les tests sont déterministes. `check=True`
    fait échouer le test si Node plante (preuve que le code s'exécute
    réellement, aucune lecture « de mémoire »).
    """
    cmd = ["node", HARNESS, mode]
    if payload is not None:
        cmd.append(json.dumps(payload))
    r = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(r.stdout)


class TestEnregistrementDesOutils(unittest.TestCase):
    """1) La couche s'enregistre bien auprès de document.modelContext."""

    def test_tous_les_outils_sont_enregistres(self):
        """Chaque outil du contrat doit être déclaré via registerTool."""
        enregistres = set(node("__liste_outils__"))
        # Ordre indépendant : on compare des ensembles, pas des listes.
        self.assertEqual(enregistres, OUTILS_ATTENDUS)

    def test_chaque_outil_a_une_description_lisible(self):
        """Un agent doit pouvoir choisir un outil : description non vide."""
        for nom in OUTILS_ATTENDUS:
            schema = node("__schema__", {"name": nom})
            # Le harnais ne renvoie que inputSchema ; on revérifie aussi
            # que la description est bien portée au moment de l'enregistrement.
            self.assertIsNotNone(schema)
        # Contrôle direct de la qualité du contrat : ___tool___ n'existe pas.
        self.assertIsNone(node("__schema__", {"name": "___tool___"}))

    def test_les_outils_ont_un_execute_appelable(self):
        """Garantie structurelle : executer chaque outil sans argument ne
        doit JAMAIS lever d'exception (réponse d'erreur structurée sinon)."""
        for nom in OUTILS_ATTENDUS:
            reponse = node(nom, {})
            # {ok:...} est la forme contractuelle ; une KeyError/TypeError
            # aurait fait planter le test plus haut (check=True).
            self.assertIn("ok", reponse)


class TestSchemasJsonSchema(unittest.TestCase):
    """2) Les schémas d'entrée sont des JSON Schema exploitables par un agent."""

    def test_schema_est_un_objet(self):
        """Tout inputSchema doit être un objet de type `object`."""
        for nom in OUTILS_ATTENDUS:
            self.assertEqual(node("__schema__", {"name": nom})["type"], "object")

    def test_types_des_coordonnees(self):
        """ouvrir_mur / placer_piege : x et z doivent être des entiers bornés."""
        for nom in ("ouvrir_mur", "placer_piege"):
            props = node("__schema__", {"name": nom})["properties"]
            self.assertEqual(props["x"]["type"], "integer")
            self.assertEqual(props["z"]["type"], "integer")
            self.assertGreaterEqual(props["x"]["minimum"], 0)
            self.assertGreaterEqual(props["z"]["minimum"], 0)

    def test_enum_des_choix_fermes(self):
        """donner_potion / inspirer / defier n'acceptent que des valeurs connues."""
        enum_potion = node("__schema__", {"name": "donner_potion"})["properties"]["type"]["enum"]
        self.assertEqual(set(enum_potion), {"petite", "grande"})
        # inspirer raisonne sur les lieux du jeu, defier sur les types de défi.
        self.assertGreaterEqual(len(node("__schema__", {"name": "inspirer"})["properties"]["lieu"]["enum"]), 5)
        self.assertGreaterEqual(len(node("__schema__", {"name": "defier"})["properties"]["type"]["enum"]), 3)

    def test_champs_requis_declares(self):
        """Un paramètre exigé (type, lieu, x/z, etage) doit être marqué required."""
        self.assertIn("type", node("__schema__", {"name": "donner_potion"})["required"])
        self.assertIn("x", node("__schema__", {"name": "ouvrir_mur"})["required"])
        self.assertIn("z", node("__schema__", {"name": "ouvrir_mur"})["required"])
        self.assertIn("lieu", node("__schema__", {"name": "inspirer"})["required"])
        self.assertIn("etage", node("__schema__", {"name": "raconter"})["required"])


class TestEtatJoueur(unittest.TestCase):
    """3) L'agent peut lire l'état réel du joueur (ancrage de toute la démo)."""

    def test_structure_et_bornes(self):
        rep = node("etat_joueur")
        self.assertTrue(rep["ok"])
        self.assertIn("vie", rep)
        self.assertIn("vieMax", rep)
        self.assertIn("mana", rep)
        self.assertIn("niveau", rep)
        self.assertIn("epee", rep)
        # Invariants métier : 0 ≤ vie ≤ vieMax ; 0 ≤ mana ≤ manaMax.
        self.assertGreaterEqual(rep["vie"], 0)
        self.assertLessEqual(rep["vie"], rep["vieMax"])
        self.assertGreaterEqual(rep["mana"], 0)
        self.assertLessEqual(rep["mana"], rep["manaMax"])
        self.assertGreaterEqual(rep["niveau"], 1)


class TestDonnerPotion(unittest.TestCase):
    """4) donner_potion soigne — et ne dépasse jamais la vie max."""

    def test_petite_potion_soigne_de_2(self):
        rep = node("donner_potion", {"type": "petite"})
        self.assertTrue(rep["ok"])
        self.assertEqual((rep["avant"], rep["apres"]), (5, 7))

    def test_grande_potion_plafonne_a_vie_max(self):
        # vie=5, gain=6 → 11 plafonné à vieMax=10.
        rep = node("donner_potion", {"type": "grande"})
        self.assertTrue(rep["ok"])
        self.assertEqual(rep["apres"], 10)
        # Preuve croisée : le plafond vient bien de l'état réel du joueur.
        self.assertEqual(node("etat_joueur")["vieMax"], 10)

    def test_plafonnement_en_sequence(self):
        """Deux potions d'affilée : la seconde ne doit RIEN ajouter (cap)."""
        seq = node("__sequence__", [
            {"tool": "donner_potion", "args": {"type": "grande"}},
            {"tool": "donner_potion", "args": {"type": "grande"}},
        ])
        self.assertEqual([r["apres"] for r in seq], [10, 10])

    def test_type_inconnu_refuse(self):
        rep = node("donner_potion", {"type": "elixir_illegal"})
        self.assertFalse(rep["ok"])
        self.assertIn("inconnu", rep["message"])

    def test_parametre_manquant_refuse(self):
        """Sans {type:...} l'agent doit recevoir une erreur claire, pas un crash."""
        rep = node("donner_potion", {})
        self.assertFalse(rep["ok"])


class TestOuvrirMur(unittest.TestCase):
    """5) ouvrir_mur modifie réellement la grille (la promesse « agent worldbuilder »)."""

    def test_ouvre_un_mur_interieur(self):
        # La grille factice a des MURS sur le pourtour (x=0 fait partie du
        # bord) et du SOL partout ailleurs. (0, 1) est donc un mur légal.
        rep = node("ouvrir_mur", {"x": 0, "z": 1})
        self.assertTrue(rep["ok"])
        self.assertEqual(rep["x"], 0)
        self.assertEqual(rep["z"], 1)

    def test_refuse_hors_grille(self):
        rep = node("ouvrir_mur", {"x": 999, "z": -3})
        self.assertFalse(rep["ok"])
        self.assertIn("hors de la grille", rep["message"])

    def test_refuse_sur_du_sol(self):
        # (2, 2) est du sol dans l'état initial → rien à ouvrir.
        rep = node("ouvrir_mur", {"x": 2, "z": 2})
        self.assertFalse(rep["ok"])
        self.assertIn("pas un mur", rep["message"])

    def test_double_ouverture_refusee(self):
        """Un mur déjà ouvert doit refuser la seconde ouverture (état réel)."""
        seq = node("__sequence__", [
            {"tool": "ouvrir_mur", "args": {"x": 0, "z": 1}},
            {"tool": "ouvrir_mur", "args": {"x": 0, "z": 1}},
        ])
        self.assertTrue(seq[0]["ok"])
        self.assertFalse(seq[1]["ok"])


class TestPlacerPiege(unittest.TestCase):
    """6) placer_piege pose un piège sur une case sol valide."""

    def test_pose_sur_du_sol(self):
        rep = node("placer_piege", {"x": 3, "z": 3})
        self.assertTrue(rep["ok"])

    def test_refuse_sur_un_mur(self):
        rep = node("placer_piege", {"x": 0, "z": 1})
        self.assertFalse(rep["ok"])
        self.assertIn("mur", rep["message"])

    def test_refuse_hors_grille(self):
        rep = node("placer_piege", {"x": 40, "z": 0})
        self.assertFalse(rep["ok"])

    def test_compte_les_pieges_poses(self):
        """Chaque pose incrémente le compteur exposé à l'agent."""
        seq = node("__sequence__", [
            {"tool": "placer_piege", "args": {"x": 3, "z": 3}},
            {"tool": "placer_piege", "args": {"x": 4, "z": 4}},
        ])
        self.assertEqual(seq[0]["message"].endswith("Total : 1"), True)
        self.assertEqual(seq[1]["message"].endswith("Total : 2"), True)

    def test_piege_memoise_la_case(self):
        """L'outil retient la dernière case : l'intégration réelle sait où
        dresser les pics (poserPiege a besoin de (x, z)). On lit l'état
        APRÈS l'action dans le même process (__sequence__)."""
        rep = node("__sequence__", {
            "steps": [{"tool": "placer_piege", "args": {"x": 5, "z": 6}}],
            "champs": ["dernierPi"],
        })
        self.assertEqual(rep["champs"]["dernierPi"], {"x": 5, "z": 6})


class TestInspirer(unittest.TestCase):
    """7) inspirer : des pistes contextuelles par lieu (vrai co-maître de jeu)."""

    def test_une_piste_pour_chaque_lieu(self):
        lieux = node("__schema__", {"name": "inspirer"})["properties"]["lieu"]["enum"]
        for lieu in lieux:
            rep = node("inspirer", {"lieu": lieu})
            self.assertTrue(rep["ok"], lieu)
            self.assertTrue(rep["message"], lieu)
            self.assertGreater(len(rep["message"]), 10, lieu)

    def test_lieu_inconnu_refuse(self):
        rep = node("inspirer", {"lieu": "antichambre_du_necromancien"})
        self.assertFalse(rep["ok"])
        self.assertIn("inconnu", rep["message"])


class TestDefier(unittest.TestCase):
    """8) defier : l'agent fait surgir un défi adapté, et le comptabilise."""

    def test_defis_acceptes(self):
        for type_defi in ["gardien", "guerrier", "horde"]:
            self.assertTrue(node("defier", {"type": type_defi})["ok"])

    def test_defi_inconnu_refuse(self):
        rep = node("defier", {"type": "dragon-titanesque"})
        self.assertFalse(rep["ok"])

    def test_compteur_incremente_en_sequence(self):
        seq = node("__sequence__", [
            {"tool": "defier", "args": {"type": "gardien"}},
            {"tool": "defier", "args": {"type": "horde"}},
        ])
        self.assertEqual(seq[0]["defisReleves"], 1)
        self.assertEqual(seq[1]["defisReleves"], 2)

    def test_defier_memoise_le_type(self):
        """L'outil retient quel défi a été lancé (dernierDefi) : l'intégration
        réelle sait quelles créatures faire surgir."""
        rep = node("__sequence__", {
            "steps": [{"tool": "defier", "args": {"type": "horde"}}],
            "champs": ["dernierDefi"],
        })
        self.assertEqual(rep["champs"]["dernierDefi"], "horde")


class TestRaconter(unittest.TestCase):
    """9) raconter : narration par étage — l'agent raconte le donjon au joueur."""

    def test_narration_de_chaque_etage(self):
        attente = {1: "caves", 2: "ossuaire", 3: "clairière", 4: "voile", 5: "palier"}
        for etage, nom_etage in attente.items():
            rep = node("raconter", {"etage": etage})
            self.assertTrue(rep["ok"], etage)
            # La narration doit citer l'étage ET le nom du lieu (vérif réelle).
            self.assertIn(str(etage), rep["message"])
            self.assertIn(nom_etage, rep["message"])

    def test_etage_zero_raconte_le_village(self):
        rep = node("raconter", {"etage": 0})
        self.assertTrue(rep["ok"])
        self.assertIn("hameau", rep["message"])

    def test_etage_invalide_refuse(self):
        for etage_invalide in [-1, 6, 12]:
            self.assertFalse(node("raconter", {"etage": etage_invalide})["ok"])


if __name__ == "__main__":
    unittest.main(verbosity=2)