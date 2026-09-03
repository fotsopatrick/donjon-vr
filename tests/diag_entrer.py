#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DIAG: pourquoi le bouton "Entrer" (#jouer) ne se laisse pas cliquer sur la
# page KOTOAGE en ligne (GCS). Réutilise lancer()/CDPSocket du test live_cdp
# (importable car main() est sous if __name__), puis sonde l'état du jeu.
import importlib.util, sys, time, os
URL = "https://storage.googleapis.com/kotoage-webmcp-20260901-133904/index.html"
spec = importlib.util.spec_from_file_location("lcd", "/home/orel/donjon-vr/tests/test_webmcp_live_cdp.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)   # safe : main() non appelé

lancer = m.lancer
proc = None
try:
    d, proc, sock = lancer()
    # aller sur la page GCS
    sock.send("Page.navigate", {"url": URL})
    time.sleep(10)   # laisser le démarrage / echec se produire

    def ev(expr):
        try:
            return sock.send("Runtime.evaluate", {"expression": expr, "returnByValue": True}).get("result", {}).get("value")
        except Exception as e:
            return "ERR:"+str(e)

    print("== etat bouton #jouer ==")
    print("  texte  :", ev("document.querySelector('#jouer') ? document.querySelector('#jouer').textContent : 'ABSENT'"))
    print("  disabled:", ev("document.querySelector('#jouer') ? document.querySelector('#jouer').disabled : 'n/a'"))
    print("== rendu/trois ==")
    print("  canvas :", ev("document.querySelectorAll('canvas').length"))
    print("  window.__webmcpConnexion :", ev("typeof window.__webmcpConnexion"))
    print("  modelesPrets :", ev("typeof modelesPrets!=='undefined' ? modelesPrets : 'indefini'"))
    print("== erreurs globales remontees ==")
    print("  window.__derrr :", ev("typeof window.__derrr!=='undefined' ? window.__derrr : 'aucune'"))
    print("== body / menu ==")
    print("  #titre classes:", ev("document.getElementById('titre') ? document.getElementById('titre').className : 'n/a'"))
finally:
    try:
        proc.kill()
    except Exception:
        pass
    try:
        import shutil
        shutil.rmtree(d, ignore_errors=True)
    except Exception:
        pass
    # assurer la fermeture du chrome de test
    os.system("pkill -9 -f '/opt/google/chrome/chrome --headless=new' >/dev/null 2>&1" )