# -*- coding: utf-8 -*-
"""La Vieille Sorcière — un test par règle, dans les deux sens.

Écrits AVANT le code (compétence Jimmy) : ils doivent d'abord échouer.
Le contrat est dans SPEC-SORCIERE.md. Aucune horloge, aucun hasard :
même offre, même réponse, toujours.
"""
import json
import os
import subprocess
import unittest

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
MODULE = os.path.join(RACINE, "webmcp", "sorciere.js")


def sorciere(appels, joueur=None):
    """Rejoue une suite d'offres sur UNE sorcière, et rend ses réponses.

    `appels` : liste de dicts, chacun passé tel quel à marchander().
    `joueur`  : 'clone' pour jouer le Clone, sinon n'importe qui d'autre.
    """
    script = """
const S = require(%s);
const s = S.creerSorciere(%s);
const sorties = [];
for (const a of %s) sorties.push(S.marchander(s, a));
console.log(JSON.stringify(sorties));
""" % (json.dumps(MODULE), json.dumps(joueur), json.dumps(appels))
    r = subprocess.run(["node", "-e", script], capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError("node a echoue : " + (r.stderr or "")[:400])
    return json.loads(r.stdout.strip().splitlines()[-1])


class TestCatalogue(unittest.TestCase):
    def test_sans_argument_elle_liste_ses_armes(self):
        rep = sorciere([{}])[0]
        self.assertTrue(rep["ok"])
        noms = [a["nom"] for a in rep["armes"]]
        self.assertIn("dague", noms)
        self.assertIn("epee", noms)
        self.assertIn("hache", noms)
        self.assertIn("baton", noms)

    def test_elle_annonce_le_prix_dune_arme(self):
        rep = sorciere([{"arme": "epee"}])[0]
        self.assertTrue(rep["ok"])
        self.assertEqual(rep["prix"], 90)
        self.assertFalse(rep["vendu"])

    def test_arme_inconnue_refusee(self):
        rep = sorciere([{"arme": "bazooka", "offre": 1000}])[0]
        self.assertFalse(rep["ok"])
        self.assertFalse(rep["vendu"])


class TestMarchandage(unittest.TestCase):
    def test_offre_au_prix_demande_elle_vend_contente(self):
        rep = sorciere([{"arme": "epee", "offre": 90}])[0]
        self.assertTrue(rep["vendu"])
        self.assertEqual(rep["patience"], 3)          # elle ne perd rien
        self.assertIn("compter", rep["message"])

    def test_offre_au_dessus_du_prix_elle_vend_aussi(self):
        rep = sorciere([{"arme": "epee", "offre": 200}])[0]
        self.assertTrue(rep["vendu"])
        self.assertEqual(rep["patience"], 3)

    def test_offre_entre_plancher_et_prix_elle_vend_en_ralant(self):
        # plancher de l'epee = 81
        rep = sorciere([{"arme": "epee", "offre": 85}])[0]
        self.assertTrue(rep["vendu"])
        self.assertEqual(rep["patience"], 2)          # elle perd 1
        self.assertIn("voles", rep["message"])

    def test_offre_pile_au_plancher_elle_vend(self):
        rep = sorciere([{"arme": "epee", "offre": 81}])[0]
        self.assertTrue(rep["vendu"])

    def test_offre_sous_le_plancher_refusee_et_le_prix_monte(self):
        reps = sorciere([{"arme": "epee", "offre": 40},
                         {"arme": "epee"}])
        self.assertFalse(reps[0]["vendu"])
        self.assertEqual(reps[0]["patience"], 2)
        self.assertIn("insulte", reps[0]["message"])
        self.assertEqual(reps[1]["prix"], 99)         # 90 + 10 %, arrondi en haut

    def test_elle_ne_descend_jamais_sous_le_plancher(self):
        # trois offres basses d'affilee : jamais vendu
        reps = sorciere([{"arme": "dague", "offre": 1},
                         {"arme": "dague", "offre": 2},
                         {"arme": "dague", "offre": 3}])
        for r in reps:
            self.assertFalse(r["vendu"], r)


class TestEmbrouille(unittest.TestCase):
    def test_trois_offres_trop_basses_et_elle_sembrouille(self):
        reps = sorciere([{"arme": "epee", "offre": 10},
                         {"arme": "epee", "offre": 10},
                         {"arme": "epee", "offre": 10},
                         {"arme": "epee", "offre": 10000}])
        self.assertEqual(reps[2]["patience"], 0)
        self.assertIn("Dehors", reps[3]["message"])
        self.assertFalse(reps[3]["vendu"])   # meme une offre enorme ne passe plus

    def test_apres_lembrouille_elle_ne_vend_plus_rien(self):
        reps = sorciere([{"arme": "epee", "offre": 1},
                         {"arme": "epee", "offre": 1},
                         {"arme": "epee", "offre": 1},
                         {"arme": "dague", "offre": 9999}])
        self.assertFalse(reps[3]["vendu"])


class TestDeterminisme(unittest.TestCase):
    def test_meme_offre_meme_reponse(self):
        a = sorciere([{"arme": "hache", "offre": 170}])[0]
        b = sorciere([{"arme": "hache", "offre": 170}])[0]
        self.assertEqual(a, b)

    def test_une_arme_vendue_ne_se_revend_pas(self):
        reps = sorciere([{"arme": "dague", "offre": 30},
                         {"arme": "dague", "offre": 30}])
        self.assertTrue(reps[0]["vendu"])
        self.assertFalse(reps[1]["vendu"])
        self.assertIn("plus rien", reps[1]["message"])


class TestLeClone(unittest.TestCase):
    """Le Clone est le SEUL avec qui elle ne s'embrouille pas vite."""

    def test_le_clone_a_plus_de_patience(self):
        rep = sorciere([{"arme": "epee"}], joueur="clone")[0]
        self.assertEqual(rep["patience"], 6)

    def test_les_autres_gardent_trois_patiences(self):
        rep = sorciere([{"arme": "epee"}], joueur="patrick")[0]
        self.assertEqual(rep["patience"], 3)

    def test_le_clone_obtient_un_prix_que_les_autres_nobtiennent_pas(self):
        # 70 sur une epee a 90 : sous le plancher de tout le monde (81),
        # mais au-dessus du plancher du Clone (68).
        autre = sorciere([{"arme": "epee", "offre": 70}], joueur="patrick")[0]
        clone = sorciere([{"arme": "epee", "offre": 70}], joueur="clone")[0]
        self.assertFalse(autre["vendu"])
        self.assertTrue(clone["vendu"])

    def test_avec_le_clone_une_offre_basse_ne_fait_pas_monter_le_prix(self):
        reps = sorciere([{"arme": "epee", "offre": 10},
                         {"arme": "epee"}], joueur="clone")
        self.assertFalse(reps[0]["vendu"])
        self.assertEqual(reps[1]["prix"], 90)      # inchange

    def test_elle_ne_descend_pas_non_plus_sous_le_plancher_du_clone(self):
        rep = sorciere([{"arme": "epee", "offre": 60}], joueur="clone")[0]
        self.assertFalse(rep["vendu"])             # 60 < 68

    def test_elle_lui_parle_autrement(self):
        rep = sorciere([{"arme": "dague", "offre": 30}], joueur="clone")[0]
        self.assertTrue(rep["vendu"])
        self.assertIn("valent les choses", rep["message"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
