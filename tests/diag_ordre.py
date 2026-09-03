#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Observe l'ORDRE réel d'apparition de KOTOAGE_WEBMCP et __webmcpConnexion sur
# la page live, + les erreurs JS non capturées. Mesure, ne devine pas.
import importlib.util, time, sys
URL = "https://storage.googleapis.com/kotoage-webmcp-20260901-133904/index.html"
spec = importlib.util.spec_from_file_location("lcd", "/home/orel/donjon-vr/tests/test_webmcp_live_cdp.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
lancer = m.lancer
proc = d = None
try:
    d, proc, sock = lancer()
    sock.send("Page.enable")
    sock.send("Runtime.enable")
    # log l'ordre d'apparition sur chaque nouvelle page
    tracer = r"""
    (() => {
      const seq = [];
      window.__kotoageTrace = seq;
      const champ = (n, v) => { seq.push(n + "@" + (typeof v)); };
      const check = () => {
        if (window.KOTOAGE_WEBMCP && !seq.includes('K')) { seq.push('K'); }
        if (window.__webmcpConnexion && !seq.includes('C')) { seq.push('C'); }
        if (window.__webmcpActif && !seq.includes('A')) { seq.push('A'); }
      };
      check();
      const iv = setInterval(check, 100);
      window.addEventListener('webmcp', () => check());
      // capture erreurs
      window.__kotoageErr = [];
      window.addEventListener('error', (e) => { window.__kotoageErr.push(String(e.message||e.error)); });
      window._t = () => { clearInterval(iv); return JSON.stringify({seq: seq, err: window.__kotoageErr}); };
    })()
    """
    sock.send("Page.addScriptToEvaluateOnNewDocument", {"source": tracer})
    sock.send("Page.navigate", {"url": URL, "transitionType": "typed"})
    print("chargement...", flush=True)
    time.sleep(14)
    r = sock.send("Runtime.evaluate", {"expression": "window._t()", "returnByValue": True})
    print("RESULTAT:", r.get("result", {}).get("value"), flush=True)
    # etat bouton final
    bouton = sock.send("Runtime.evaluate", {"expression": "document.getElementById('jouer')?{t:document.getElementById('jouer').textContent,d:document.getElementById('jouer').disabled}:null", "returnByValue": True})
    print("BOUTON:", bouton.get("result", {}).get("value"), flush=True)
finally:
    try: proc.kill()
    except Exception: pass
    try: import shutil; shutil.rmtree(d, ignore_errors=True)
    except Exception: pass