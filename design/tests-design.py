# -*- coding: utf-8 -*-
"""
tests-design.py — LES TESTS DE DESIGN de KOTOAGE.

Ne teste pas le code (ça, c'est test-jeu.js) mais le RENDU : est-ce que ce qu'on
voit à l'écran colle au goût de Patrick ? Chaque test est une assertion chiffrée
sur la palette, plus l'algo de comparaison (design_lib) qui tranche cyberpunk vs
plaine verte, et une distance à deux images de référence.

Usage :
  python3 tests-design.py                      # capture l'arène en direct puis teste
  python3 tests-design.py image.png            # teste une capture déjà prise
"""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import design_lib as D

ICI = os.path.dirname(os.path.abspath(__file__))
REF_CYBER  = os.path.join(ICI,'refs','ref-cyberpunk.png')
REF_PLAINE = os.path.join(ICI,'refs','ref-plaine-verte.png')

def capturer_arene():
    out = os.path.join(ICI,'refs','arene-courante.png')
    print("→ capture de l'arène en direct (Chrome headless)…", flush=True)
    r = subprocess.run(['node', os.path.join(ICI,'capturer.js'),
                        'http://localhost:8091/#arene', out],
                       capture_output=True, text=True)
    if r.returncode!=0 or not os.path.exists(out):
        print("capture impossible :", r.stderr[:300]); sys.exit(2)
    return out

ok=0; ko=0
def test(nom, cond, detail=''):
    global ok,ko
    if cond: ok+=1; print("  ✅", nom, detail)
    else:    ko+=1; print("  ❌", nom, detail)

def main():
    img = sys.argv[1] if len(sys.argv)>1 else capturer_arene()
    px  = D.pixels(img, pas=4)
    sc  = D.score_palettes(px)
    fr  = sc['fractions']; L = sc['luminance']
    neon = fr.get('cyan',0)+fr.get('magenta',0)+fr.get('ambre',0)
    d_cyber  = D.distance_hist(px, D.pixels(REF_CYBER,4))
    d_plaine = D.distance_hist(px, D.pixels(REF_PLAINE,4))

    print("\nMESURES arène :", sc)
    print(f"néon total={neon:.4f}  dist→cyber={d_cyber}  dist→plaine={d_plaine}\n")

    print("TESTS DE DESIGN (goût Patrick : cyberpunk néon nocturne, pas de plaine verte)")
    test("nuit — image sombre (lum<70)",              L < 70,               f"(lum={L})")
    test("fond sombre dominant (>50%)",               fr.get('sombre',0) > 0.50, f"({fr.get('sombre',0):.2%})")
    test("néon présent (cyan+magenta+ambre >0.3%)",   neon > 0.003,         f"({neon:.2%})")
    test("magenta présent (>0.1%)",                   fr.get('magenta',0) > 0.001, f"({fr.get('magenta',0):.2%})")
    test("pas de plaine verte (vert <3%)",            fr.get('vert',0) < 0.03, f"({fr.get('vert',0):.2%})")
    test("ALGO palettes : verdict = cyberpunk",       sc['verdict']=='cyberpunk', f"(cyber={sc['cyberpunk']} vs plaine={sc['plaine_verte']})")
    test("ALGO comparaison : plus proche du cyberpunk que de la plaine",
                                                       d_cyber < d_plaine,   f"({d_cyber} < {d_plaine})")
    test("ressemblance forte au cyberpunk de réf (dist<0.4)", d_cyber < 0.40, f"({d_cyber})")

    print(f"\n  {ok} réussis, {ko} échoués")
    sys.exit(1 if ko else 0)

if __name__=='__main__':
    main()
