# -*- coding: utf-8 -*-
"""BONNE ÉTOILE — la compétence unique du Clone.

Écrits AVANT le code (compétence Jimmy). Contrat : SPEC-SORCIERE.md.
Un coup fatal, une fois par partie, et seulement pour le Clone.
"""
import json
import os
import subprocess
import unittest

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
MODULE = os.path.join(RACINE, "webmcp", "clone.js")


def coups(joueur, vie, degats_successifs):
    """Encaisse une suite de coups et rend l'état après chacun."""
    script = """
const C = require(%s);
const p = C.creerPorteur(%s, %s);
const sorties = [];
for (const d of %s) sorties.push(C.encaisser(p, d));
console.log(JSON.stringify(sorties));
""" % (json.dumps(MODULE), json.dumps(joueur), json.dumps(vie),
       json.dumps(degats_successifs))
    r = subprocess.run(["node", "-e", script], capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError("node a echoue : " + (r.stderr or "")[:400])
    return json.loads(r.stdout.strip().splitlines()[-1])


class TestBonneEtoile(unittest.TestCase):
    def test_un_coup_non_fatal_ne_declenche_rien(self):
        r = coups("clone", 10, [4])[0]
        self.assertEqual(r["vie"], 6)
        self.assertFalse(r["declenchee"])
        self.assertTrue(r["disponible"])       # elle est toujours en reserve

    def test_le_coup_fatal_laisse_le_clone_a_un_point_de_vie(self):
        r = coups("clone", 10, [99])[0]
        self.assertTrue(r["declenchee"])
        self.assertEqual(r["vie"], 1)
        self.assertFalse(r["mort"])
        self.assertIn("Pas aujourd", r["message"])

    def test_elle_ne_sert_qu_une_fois(self):
        rs = coups("clone", 10, [99, 99])
        self.assertTrue(rs[0]["declenchee"])
        self.assertFalse(rs[1]["declenchee"])
        self.assertTrue(rs[1]["mort"])
        self.assertEqual(rs[1]["vie"], 0)

    def test_les_autres_joueurs_meurent(self):
        r = coups("patrick", 10, [99])[0]
        self.assertFalse(r["declenchee"])
        self.assertTrue(r["mort"])
        self.assertEqual(r["vie"], 0)

    def test_un_coup_pile_mortel_compte_comme_fatal(self):
        r = coups("clone", 10, [10])[0]
        self.assertTrue(r["declenchee"])
        self.assertEqual(r["vie"], 1)

    def test_plusieurs_petits_coups_puis_le_fatal(self):
        rs = coups("clone", 10, [3, 3, 3, 3])
        self.assertEqual(rs[0]["vie"], 7)
        self.assertEqual(rs[2]["vie"], 1)
        self.assertTrue(rs[3]["declenchee"])   # le 4e coup l'aurait tue
        self.assertEqual(rs[3]["vie"], 1)

    def test_meme_coup_meme_resultat(self):
        a = coups("clone", 8, [50])[0]
        b = coups("clone", 8, [50])[0]
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main(verbosity=2)
