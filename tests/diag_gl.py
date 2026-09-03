#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Test WebGL minimal en headless : charge gl-check.html et lit document.title.
import importlib.util, time
# reutilise lancer/CDPSocket du test (importable)
spec = importlib.util.spec_from_file_location("lcd", "/home/orel/donjon-vr/tests/test_webmcp_live_cdp.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
import subprocess, tempfile, os, socket, json, urllib.request
PORT = 9333
CHROME = m.CHROME
d = tempfile.mkdtemp(prefix="kotoage-gl-")
p = None
try:
    p = subprocess.Popen([CHROME, "--headless=new", "--no-sandbox",
        "--use-gl=swiftshader","--use-angle=swiftshader","--enable-unsafe-swiftshader",
        "--user-data-dir="+d, "--remote-debugging-port=%d"%PORT, "file:///tmp/opencode/gl-check.html"],
        stdout=None, stderr=None)
    for _ in range(40):
        try:
            urllib.request.urlopen("http://127.0.0.1:%d/json/version"%PORT, timeout=2).read(); break
        except Exception: time.sleep(0.25)
    tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:%d/json"%PORT, timeout=5).read())
    tab = next((t for t in tabs if t["type"]=="page"), tabs[0])
    sock = m.CDPSocket(tab["webSocketDebuggerUrl"])
    time.sleep(5)
    r = sock.send("Runtime.evaluate", {"expression":"document.title","returnByValue":True})
    print("TITLE:", r.get("result",{}).get("value"))
finally:
    try: p and p.kill()
    except Exception: pass
    import shutil; shutil.rmtree(d, ignore_errors=True)