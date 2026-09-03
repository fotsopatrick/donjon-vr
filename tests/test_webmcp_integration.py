# -*- coding: utf-8 -*-
# =====================================================================
#  tests/test_webmcp_integration.py — PREUVES du pont RÉEL vers le jeu
# ---------------------------------------------------------------------
#  Ceci prouve que la couche WebMCP (webmcp/webmcp.js, pure et déjà
#  testée) branche bien les ouvriers REELS du jeu quand elle tourne dans
#  index.html. On simule la page du jeu (mêmes noms que le pont
#  __webmcpConnexion) et on charge LE code de l'intégration navigateur
#  (webmcp/integration.js) tel quel, via le harnais Node.
#
#  Chaque « effet de bord » sur le jeu est journalisé par le harnais :
#    dessinerCoeurs()  → potion mise à jour à l'écran
#    construireMurs()  → pierre reconstruite après ouverture d'un mur
#    poserPiege(x, z)  → pics dressés sur la case choisie
#    monte(type,x,z)   → créature réellement apparue (D.inspecterCreature)
#    dire(msg)         → message affiché dans le HUD du joueur
#
#  Lancement : python tests/test_webmcp_integration.py
# =====================================================================
import json
import os
import subprocess
import unittest

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARNESS = os.path.join(RACINE, "tests", "webmcp_integration_harness.js")

OUTILS_ATTENDUS = {
    "etat_joueur",
    "donner_potion",
    "ouvrir_mur",
    "placer_piege",
    "inspirer",
    "defier",
    "raconter",
    "braignak_etude",
}


def node(requete):
    """Lance le harnais d'intégration et relit sa réponse JSON."""
    arg = requete if isinstance(requete, str) else json.dumps(requete)
    r = subprocess.run(
        ["node", HARNESS, arg],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return json.loads(r.stdout)


def un_peu_de_tout(tool, args=None):
    """Message de préparation commun pour les tests d'appel."""
    return node({"action": "appel", "tool": tool, "args": args or {}})


class TestEnregistrementSurLeJeu(unittest.TestCase):
    """1) Dans la page du jeu, les 7 outils sont enregistrés sur modelContext."""

    def test_tous_les_outils_enregistres(self):
        rep = node({"action": "etat"})
        self.assertEqual(set(rep["outils"]), OUTILS_ATTENDUS)
        # Aucun effet de bord au simple enregistrement.
        self.assertEqual(rep["journal"], [])

    def test_sans_context_le_jeu_reste_intact(self):
        """Navigateur sans WebMCP : RIEN ne s'enregistre, rien ne s'exécute."""
        rep = node("sans-contexte")
        self.assertTrue(rep["muet"])
        self.assertEqual(rep["journal"], [])


class TestEtatJoueurSurLeJeu(unittest.TestCase):
    """2) L'agent lit le VRAI état : vie, niveau du personnage réel."""

    def test_lit_le_personnage_reel(self):
        rep = un_peu_de_tout("etat_joueur")
        self.assertTrue(rep["resultat"]["ok"])
        self.assertEqual(rep["resultat"]["vie"], 5)
        self.assertEqual(rep["resultat"]["niveau"], 1)
        self.assertEqual(rep["resultat"]["epee"], True)
        self.assertEqual(rep["journal"], [])


class TestDonnerPotionSurLeJeu(unittest.TestCase):
    """3) La potion soigne le vrai joueur ET rafraîchit l'écran."""

    def test_grande_potion_soigne_le_personnage(self):
        rep = un_peu_de_tout("donner_potion", {"type": "grande"})
        self.assertTrue(rep["resultat"]["ok"])
        self.assertEqual(rep["vie"], 10)                 # le vrai joueur est soigné
        self.assertIn("dessinerCoeurs", rep["journal"])  # et son HUD est refait

    def test_sequence_de_potions_cap_a_vie_max(self):
        rep = node({"action": "sequence", "steps": [
            {"tool": "donner_potion", "args": {"type": "grande"}},
            {"tool": "donner_potion", "args": {"type": "grande"}},
        ]})
        self.assertEqual(rep["vie"], 10)
        self.assertEqual([r["apres"] for r in rep["resultats"]], [10, 10])


class TestOuvrirMurSurLeJeu(unittest.TestCase):
    """4) Ouvrir un mur modifie la VRAIE grille et reconstruit la pierre."""

    def test_ouvre_et_reconstruit(self):
        # (0, 1) = mur du pourtour ; la grille factice a grid[1][0] === WALL.
        rep = un_peu_de_tout("ouvrir_mur", {"x": 0, "z": 1})
        self.assertTrue(rep["resultat"]["ok"])
        self.assertEqual(rep["caseOuverte"], 1)          # le vrai grid[1][0] est devenu sol
        self.assertIn("construireMurs", rep["journal"])  # et les murs 3D sont rebâtis

    def test_refuse_sur_du_sol_du_jeu(self):
        rep = un_peu_de_tout("ouvrir_mur", {"x": 5, "z": 5})
        self.assertFalse(rep["resultat"]["ok"])
        # Aucun effet de bord sur le jeu : grid[1][0] reste un mur (0).
        self.assertEqual(rep["caseOuverte"], 0)
        self.assertNotIn("construireMurs", rep["journal"])


class TestPlacerPiegeSurLeJeu(unittest.TestCase):
    """5) Le piège est dressé POUR DE VRAI sur la case choisie."""

    def test_pose_les_pics_sur_la_case(self):
        rep = un_peu_de_tout("placer_piege", {"x": 3, "z": 3})
        self.assertTrue(rep["resultat"]["ok"])
        # Effet réel : poserPiege a été appelée avec les bonnes coordonnées.
        self.assertIn(["poserPiege", 3, 3], rep["journal"])

    def test_refuse_sur_un_mur_sans_effet(self):
        rep = un_peu_de_tout("placer_piege", {"x": 0, "z": 1})
        self.assertFalse(rep["resultat"]["ok"])
        self.assertEqual(rep["journal"], [])


class TestDefierSurLeJeu(unittest.TestCase):
    """6) Le défi fait surgir de vraies créatures près du joueur."""

    def test_gardien_surgit(self):
        rep = un_peu_de_tout("defier", {"type": "gardien"})
        self.assertTrue(rep["resultat"]["ok"])
        monte = [j for j in rep["journal"] if j[0] == "monte"]
        self.assertEqual(len(monte), 2)
        self.assertTrue(all(m[1] == "slime_rouge" for m in monte), monte)

    def test_horde_surgit_en_trois(self):
        rep = un_peu_de_tout("defier", {"type": "horde"})
        monte = [j for j in rep["journal"] if j[0] == "monte"]
        self.assertEqual(len(monte), 3)

    def test_defi_inconnu_aucune_creature(self):
        rep = un_peu_de_tout("defier", {"type": "cyclope"})
        self.assertFalse(rep["resultat"]["ok"])
        self.assertEqual(rep["journal"], [])


class TestMessagesDansLeJeu(unittest.TestCase):
    """7) Chaque geste de l'agent s'affiche dans le HUD du joueur (dire)."""

    def test_inspiration_affichee(self):
        rep = un_peu_de_tout("inspirer", {"lieu": "caves"})
        self.assertTrue(rep["resultat"]["ok"])
        self.assertIn(["dire", rep["resultat"]["message"]], rep["journal"])

    def test_raconter_affiche_la_narration(self):
        rep = un_peu_de_tout("raconter", {"etage": 3})
        self.assertTrue(rep["resultat"]["ok"])
        self.assertIn(["dire", rep["resultat"]["message"]], rep["journal"])


class TestEnchainementReel(unittest.TestCase):
    """8) Un vrai partenariat agent-humain : soin, piège, défi, narration."""

    def test_scenario_co_maitre_de_jeu(self):
        rep = node({"action": "sequence", "steps": [
            {"tool": "raconter", "args": {"etage": 1}},
            {"tool": "donner_potion", "args": {"type": "petite"}},
            {"tool": "placer_piege", "args": {"x": 3, "z": 3}},
            {"tool": "defier", "args": {"type": "gardien"}},
        ]})
        self.assertTrue(all(r["ok"] for r in rep["resultats"]))
        evenements = [j[0] if isinstance(j, list) else j for j in rep["journal"]]
        self.assertIn("dire", evenements)          # narration affichée
        self.assertIn("dessinerCoeurs", evenements)  # potion appliquée
        self.assertIn("poserPiege", evenements)     # piège dressé
        self.assertGreaterEqual(evenements.count("monte"), 2)  # gardien surgi
        self.assertEqual(rep["vie"], 7)              # 5 + potion petite


if __name__ == "__main__":
    unittest.main(verbosity=2)